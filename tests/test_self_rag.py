"""Self-RAG 测试:自省工作流路由(确定性,替换 _invoke)。

通过替换 nodes._invoke,按「模板身份」分发脚本化 LLM 输出,
确定性验证工作流的四个分支:
    1. DIRECT   闲聊/无关 -> 不检索,直接提示
    2. 正常路径  RETRIEVE -> filter YES -> ENOUGH -> 生成
    3. 重检索    check 先 LACK -> 回到 retrieve -> 再 ENOUGH -> 生成
    4. 无有效资料 filter 全 NO -> 生成节点给提示,不调生成 LLM
"""

import io

import pytest

from app.blueprints.rag.self_rag import nodes, prompts


def _install_llm(monkeypatch, responses: list[tuple]):
    """responses: [(模板, 返回值或 callable), ...]。按模板身份(is)分发。"""

    def fake_invoke(template, **variables) -> str:
        for tpl, value in responses:
            if template is tpl:
                return str(value(variables)) if callable(value) else str(value)
        raise AssertionError(f"未脚本化的模板被调用: {template}")

    monkeypatch.setattr(nodes, "_invoke", fake_invoke)


def _upload_cases(client, fake_embedding):
    content = (
        "1 感冒・风寒束表证\n主诉:恶寒头痛 2 天。\n治法:辛温解表。\n\n"
        "2 咳嗽・痰湿蕴肺证\n主诉:咳嗽痰多 2 周。\n治法:燥湿化痰。\n"
    )
    resp = client.post(
        "/rag/knowledge/upload",
        data={"file": (io.BytesIO(content.encode("utf-8")), "病例.txt")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201


def test_self_rag_query_empty(client):
    resp = client.post("/rag/self/query", json={"query": ""})
    assert resp.status_code == 400


def test_self_rag_direct_no_retrieve(client, fake_embedding, monkeypatch):
    """闲聊 -> judge 判 DIRECT -> 不检索直接提示,retrieve_round 为 0。"""
    _install_llm(monkeypatch, [(prompts.judge_retrieve_template, "DIRECT")])

    resp = client.post("/rag/self/query", json={"query": "你好呀"})
    body = resp.get_json()

    assert "请输入与中西医相关的描述" in body["answer"]
    assert body["retrieve_round"] == 0
    assert body["sources"] == []


def test_self_rag_normal_flow(client, fake_embedding, monkeypatch):
    """问诊 -> RETRIEVE -> filter YES -> ENOUGH -> 生成答案。"""
    _upload_cases(client, fake_embedding)
    _install_llm(
        monkeypatch,
        [
            (prompts.judge_retrieve_template, "RETRIEVE"),
            (prompts.filter_docs_template, "YES"),
            (prompts.check_sufficiency_template, "ENOUGH"),
            (prompts.generate_template, "诊断:风寒束表证"),
        ],
    )

    resp = client.post("/rag/self/query", json={"query": "恶寒头痛 2 天"})
    body = resp.get_json()

    assert body["answer"] == "诊断:风寒束表证"
    assert len(body["sources"]) > 0  # 有效病例被生成节点使用
    assert body["retrieve_round"] == 1


def test_self_rag_re_retrieve_when_lack(client, fake_embedding, monkeypatch):
    """check 先 LACK -> 重检索 -> 再 ENOUGH,retrieve_round 体现多轮自省。"""
    _upload_cases(client, fake_embedding)

    check_calls = {"n": 0}

    def fake_check(variables):
        check_calls["n"] += 1
        return "LACK" if check_calls["n"] == 1 else "ENOUGH"

    _install_llm(
        monkeypatch,
        [
            (prompts.judge_retrieve_template, "RETRIEVE"),
            (prompts.filter_docs_template, "YES"),
            (prompts.check_sufficiency_template, fake_check),
            (prompts.generate_template, "诊断:风寒束表证"),
        ],
    )

    resp = client.post("/rag/self/query", json={"query": "恶寒头痛"})
    body = resp.get_json()

    assert body["answer"] == "诊断:风寒束表证"
    assert body["retrieve_round"] == 2  # 重检索了一轮


def test_self_rag_no_valid_docs(client, fake_embedding, monkeypatch):
    """filter 全 NO -> 无有效资料 -> 生成节点直接给提示,不调生成 LLM。"""
    _upload_cases(client, fake_embedding)

    def unexpected(variables):
        raise AssertionError("无有效资料时不应调用生成 LLM")

    _install_llm(
        monkeypatch,
        [
            (prompts.judge_retrieve_template, "RETRIEVE"),
            (prompts.filter_docs_template, "NO"),
            (prompts.check_sufficiency_template, unexpected),
            (prompts.generate_template, unexpected),
        ],
    )

    resp = client.post("/rag/self/query", json={"query": "头晕失眠"})
    body = resp.get_json()

    assert "暂无可参考的病例资料" in body["answer"]
    assert body["sources"] == []