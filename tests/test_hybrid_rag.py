"""Hybrid RAG 混合检索 + 生成流程测试(流式 SSE)。

与 naive_rag 的差别在检索阶段:
    向量召回候选 -> BM25 关键词重排序 -> 取 top_k。
数据同样通过 knowledge_base 接口(/rag/knowledge/*)写入。
"""

import io
import json


def _parse_sse(raw: str) -> list[dict]:
    events = []
    for line in raw.split("\n\n"):
        line = line.strip()
        if line.startswith("data: "):
            payload = line[6:]
            if payload == "[DONE]":
                events.append({"type": "done"})
            else:
                events.append(json.loads(payload))
    return events


def test_hybrid_rag_query_empty(client):
    resp = client.post("/rag/hybrid/query", json={"query": ""})
    assert resp.status_code == 400


def test_hybrid_rag_query_stream(client, fake_embedding):
    resp = client.post("/rag/hybrid/query", json={"query": "感冒症状"})
    assert resp.status_code == 200
    assert resp.mimetype == "text/event-stream"

    events = _parse_sse(resp.get_data(as_text=True))
    assert events[0]["type"] == "sources"
    assert isinstance(events[0]["sources"], list)

    delta_events = [e for e in events if e["type"] == "delta"]
    assert len(delta_events) > 0
    assert all(isinstance(e["content"], str) for e in delta_events)

    assert events[-1]["type"] == "done"


def test_hybrid_rag_full_flow(client, fake_embedding):
    content = (
        "1 感冒・风寒束表证\n主诉:恶寒头痛 2 天。\n\n"
        "2 咳嗽・痰湿蕴肺证\n主诉:咳嗽痰多 2 周。\n"
    )
    resp = client.post(
        "/rag/knowledge/upload",
        data={"file": (io.BytesIO(content.encode("utf-8")), "病例.txt")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201
    assert resp.get_json()["count"] == 2

    resp = client.post("/rag/hybrid/query", json={"query": "感冒症状"})
    assert resp.status_code == 200
    assert resp.mimetype == "text/event-stream"

    events = _parse_sse(resp.get_data(as_text=True))

    sources_event = events[0]
    assert sources_event["type"] == "sources"
    assert len(sources_event["sources"]) > 0

    delta_events = [e for e in events if e["type"] == "delta"]
    answer = "".join(e["content"] for e in delta_events)
    assert len(answer) > 0

    assert events[-1]["type"] == "done"
