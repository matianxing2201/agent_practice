"""Agentic RAG 测试:LangChain Agent(invoke)+ JSON 返回。

通过替换 services.create_agent 注入假 Agent,脚本化最终消息列表
(决策 / 观察 / 最终答案),验证返回 JSON 的:
    1. trace 数组顺序:decide -> observe
    2. sources 来自 search_local_tool 的工具结果
    3. answer 为最终答案文本
    4. GraphRecursionError -> trace(limit) 终止
    5. @tool 工具对象真实调用(本地检索走真实 Milvus)
"""

import io
import json

import pytest
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.errors import GraphRecursionError

from app.blueprints.rag.agentic_rag import services, tools


class FakeAgent:
    """假 Agent:invoke() 返回脚本化的最终消息列表。"""

    def __init__(self, messages: list):
        self._messages = messages

    def invoke(self, input, config=None):
        return {"messages": self._messages}


def _decide_message(tool_name: str, args: dict, call_id: str = "call_1") -> AIMessage:
    """AI 消息:决定调用工具。"""
    return AIMessage(
        content="",
        tool_calls=[
            {"name": tool_name, "args": args, "id": call_id, "type": "tool_call"}
        ],
    )


def _observe_message(tool_name: str, content: str, call_id: str = "call_1") -> ToolMessage:
    """工具消息:执行结果。"""
    return ToolMessage(content=content, name=tool_name, tool_call_id=call_id)


def _answer_message(content: str) -> AIMessage:
    """AI 消息:无工具调用,最终答案。"""
    return AIMessage(content=content)


@pytest.fixture
def fake_agent(monkeypatch):
    """替换 services.create_agent:返回按脚本消息列表的假 Agent。"""

    def _install(messages: list):
        monkeypatch.setattr(
            services, "create_agent", lambda *a, **k: FakeAgent(messages)
        )

    return _install


def test_agentic_rag_query_empty(client):
    resp = client.post("/rag/agentic/query", json={"query": ""})
    assert resp.status_code == 400


def test_agentic_rag_local_then_answer(client, fake_agent):
    """agent 先决策调用本地检索工具,拿到片段后给出最终答案。

    验证:trace 顺序(decide -> observe)、sources 来自工具结果、answer 为最终答案。
    """
    local_json = json.dumps(
        [{"text": "1 感冒・风寒束表证\n主诉:恶寒头痛", "score": 0.9}],
        ensure_ascii=False,
    )
    fake_agent(
        [
            _decide_message("search_local_tool", {"query": "恶寒头痛"}),
            _observe_message("search_local_tool", local_json),
            _answer_message("风寒束表证"),
        ]
    )

    resp = client.post("/rag/agentic/query", json={"query": "恶寒头痛 2 天"})
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"

    body = resp.get_json()
    trace_events = body["trace"]

    assert len(trace_events) == 2
    assert trace_events[0]["phase"] == "decide"
    assert trace_events[0]["tool"] == "search_local_tool"
    assert trace_events[0]["args"] == {"query": "恶寒头痛"}
    assert trace_events[1]["phase"] == "observe"
    assert trace_events[1]["tool"] == "search_local_tool"

    assert len(body["sources"]) == 1
    assert body["sources"][0]["text"].startswith("1 感冒")

    assert body["answer"] == "风寒束表证"


def test_agentic_rag_online_then_answer(client, fake_agent):
    """agent 决策调用联网工具;无本地检索时 sources 为空列表。"""
    online_json = json.dumps(
        [{"title": "风寒感冒", "content": "恶寒重发热轻", "url": "http://x"}],
        ensure_ascii=False,
    )
    fake_agent(
        [
            _decide_message("search_online_tool", {"query": "恶寒头痛 中医 辨证"}),
            _observe_message("search_online_tool", online_json),
            _answer_message("外感风寒"),
        ]
    )

    resp = client.post("/rag/agentic/query", json={"query": "恶寒头痛"})
    body = resp.get_json()

    trace_events = body["trace"]
    assert trace_events[0]["phase"] == "decide"
    assert trace_events[0]["tool"] == "search_online_tool"
    assert trace_events[1]["phase"] == "observe"

    assert body["sources"] == []
    assert body["answer"] == "外感风寒"


def test_agentic_rag_max_iterations(client, monkeypatch):
    """超出 recursion_limit -> GraphRecursionError -> trace(limit) 终止。"""

    class RecursionAgent:
        def invoke(self, input, config=None):
            raise GraphRecursionError("Recursion limit reached")

    monkeypatch.setattr(services, "create_agent", lambda *a, **k: RecursionAgent())

    resp = client.post("/rag/agentic/query", json={"query": "什么病"})
    body = resp.get_json()

    limit_event = [e for e in body["trace"] if e["phase"] == "limit"]
    assert len(limit_event) == 1
    assert "最大迭代次数" in limit_event[0]["message"]

    assert body["answer"] == ""


def test_search_local_tool_queries_milvus(app, client, fake_embedding):
    """@tool 工具对象真实执行:上传病历后,search_local 返回 JSON 片段列表。"""
    content = "1 感冒・风寒束表证\n主诉:恶寒头痛 2 天。\n"
    resp = client.post(
        "/rag/knowledge/upload",
        data={"file": (io.BytesIO(content.encode("utf-8")), "病例.txt")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201

    with app.app_context():
        result = tools.search_local.invoke({"query": "感冒"})

    docs = json.loads(result)
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert "text" in docs[0] and "score" in docs[0]
