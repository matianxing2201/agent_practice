"""Corrective-RAG 测试:相关性评审 + 纠错路由(确定性,替换 _invoke)。

通过替换 nodes._invoke,按模板身份分发脚本化 LLM 输出,
验证纠错路由的三个分支:
    1. 相关资料 >= MIN(2) -> 直接生成,不联网
    2. 相关资料 < MIN -> 转联网搜索补充后生成
    3. 检索为空 -> relevant 空 -> 联网路径
"""

import io
import json

import pytest

from app.blueprints.rag.corrective_rag import nodes, prompts


def _parse_sse(raw: str) -> list[dict]:
    events = []
    for line in raw.split("\n\n"):
        line = line.strip()
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


def _install_llm(monkeypatch, responses: list[tuple]):
    def fake_invoke(template, **variables) -> str:
        for tpl, value in responses:
            if template is tpl:
                return str(value(variables)) if callable(value) else str(value)
        raise AssertionError(f"未脚本化的模板被调用: {template}")

    monkeypatch.setattr(nodes, "_invoke", fake_invoke)


def _upload_cases(client, fake_embedding):
    content = (
        "1 感冒・风寒束表证\n主诉:恶寒头痛 2 天。\n治法:辛温解表。\n\n"
        "2 咳嗽・痰湿蕴肺证\n主诉:咳嗽痰多 2 周。\n治法:燥湿化痰。\n\n"
        "3 胃痛・肝气犯胃\n主诉:胃脘胀痛连胁。\n治法:疏肝理气。\n\n"
        "4 失眠・心脾两虚\n主诉:失眠多梦。\n治法:补益心脾。\n\n"
        "5 腰痛・肾虚\n主诉:腰膝酸软。\n治法:补肾壮腰。\n"
    )
    resp = client.post(
        "/rag/knowledge/upload",
        data={"file": (io.BytesIO(content.encode("utf-8")), "病例.txt")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201


def _fake_tavily(monkeypatch):
    """让真实 node_web_search 里的 TavilyClient.search 返回假结果,不联网。"""
    from tavily import TavilyClient

    def fake_search(self, query, search_depth="basic", max_results=5):
        return {"results": [{"title": "网诊", "content": "补充信息", "url": "http://x"}]}

    monkeypatch.setattr(TavilyClient, "search", fake_search)


def test_corrective_rag_query_empty(client):
    resp = client.post("/rag/corrective/query", json={"query": ""})
    assert resp.status_code == 400


def test_corrective_rag_enough_relevant_no_web(client, fake_embedding, monkeypatch):
    """检索 5 条,评审 5 条都相关 -> relevant >= 2 -> 直接生成,不联网。"""
    _upload_cases(client, fake_embedding)

    _install_llm(
        monkeypatch,
        [
            (prompts.grade_milvus_docs_template, "relevant"),
            (prompts.generate_answer_template, "诊断:风寒束表证"),
        ],
    )

    # mock Tavily:若意外走到联网,会立刻失败(断言足够资料时不该联网)
    def boom_search(self, query, search_depth="basic", max_results=5):
        raise AssertionError("相关资料足够,不应调用 Tavily")

    from tavily import TavilyClient
    monkeypatch.setattr(TavilyClient, "search", boom_search)

    resp = client.post("/rag/corrective/query", json={"query": "恶寒头痛"})
    events = _parse_sse(resp.get_data(as_text=True))
    answer = "".join(e["content"] for e in events if "content" in e)

    assert answer == "诊断:风寒束表证"
    assert events[-1] == {"done": True}


def test_corrective_rag_insufficient_goes_web(client, fake_embedding, monkeypatch):
    """评审只有 1 条相关 -> relevant < 2 -> 转联网补充后生成。"""
    _upload_cases(client, fake_embedding)

    grade_calls = {"n": 0}

    def fake_grade(variables):
        grade_calls["n"] += 1
        return "relevant" if grade_calls["n"] == 1 else "irrelevant"

    _install_llm(
        monkeypatch,
        [
            (prompts.grade_milvus_docs_template, fake_grade),
            (prompts.generate_answer_template, "诊断:联网补充后生成"),
        ],
    )
    _fake_tavily(monkeypatch)

    resp = client.post("/rag/corrective/query", json={"query": "头晕"})
    events = _parse_sse(resp.get_data(as_text=True))
    answer = "".join(e["content"] for e in events if "content" in e)

    assert answer == "诊断:联网补充后生成"
    assert grade_calls["n"] == 5  # 5 条候选都评审了
    assert events[-1] == {"done": True}


def test_corrective_rag_empty_kb_goes_web(client, fake_embedding, monkeypatch):
    """知识库为空 -> milvus_docs 空 -> relevant 空 -> 走联网。"""
    # 不上传数据,知识库为空

    _install_llm(
        monkeypatch,
        [(prompts.generate_answer_template, "诊断:纯联网")],
    )
    _fake_tavily(monkeypatch)

    resp = client.post("/rag/corrective/query", json={"query": "恶寒头痛"})
    events = _parse_sse(resp.get_data(as_text=True))
    answer = "".join(e["content"] for e in events if "content" in e)

    assert answer == "诊断:纯联网"
    assert events[-1] == {"done": True}