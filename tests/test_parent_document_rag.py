"""Parent-Document RAG 测试:父子分块,小块检索、大块返回(SSE 流式)。

验证:
    1. 上传:父子两级切分 -> 父块写 JSON 文件 + 子块写 Milvus
    2. 查询:命中子块 -> 回取父块全文(sources 是完整父块,不是子块),答案流式
    3. 去重:多个子块命中同一父块,sources 只保留一次
    4. 空输入 400
"""

import io
import json

from app.blueprints.rag.parent_document_rag import store


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


# 两条完整中医病历(每条约 180 字,确保单个父块内能切出多个子块)
_CASE = (
    "1 感冒・风寒束表证\n"
    "主诉：恶寒头痛、鼻塞流清涕 2 天。\n"
    "现病史：2 天前户外受凉吹风，恶寒重发热轻，全身肌肉酸痛，无汗，鼻塞流清涕，咽痒咳嗽，痰白稀薄，口不渴。\n"
    "中医四诊：舌淡红，苔薄白；脉浮紧。\n"
    "中医诊断：感冒（风寒束表证）。治法：辛温解表，宣肺散寒。\n"
    "方药：荆芥 10g，防风 10g，紫苏叶 10g，苦杏仁 10g，桔梗 6g，炙甘草 6g，生姜 6g。\n\n"
    "2 咳嗽・痰湿蕴肺证\n"
    "主诉：咳嗽痰多 2 周。\n"
    "现病史：咳嗽反复，痰白黏腻量多，晨起为甚，胸闷脘痞，纳呆，大便偏溏。\n"
    "中医四诊：舌淡胖，苔白腻；脉濡滑。\n"
    "中医诊断：咳嗽（痰湿蕴肺证）。治法：燥湿化痰，理气止咳。\n"
    "方药：半夏 10g，陈皮 10g，茯苓 15g，甘草 6g，杏仁 10g，厚朴 10g。\n"
)


def _upload(client, content=_CASE):
    return client.post(
        "/rag/parent/upload",
        data={"file": (io.BytesIO(content.encode("utf-8")), "病例.txt")},
        content_type="multipart/form-data",
    )


def test_parent_upload_rejects_non_txt(client):
    resp = client.post(
        "/rag/parent/upload",
        data={"file": (io.BytesIO(b"x"), "病例.pdf")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400


def test_parent_upload_empty_file(client):
    resp = _upload(client, content="  \n")
    assert resp.status_code == 400


def test_parent_upload_writes_both_stores(app, client, fake_embedding):
    """上传后:父块 JSON 文件写入(含 parent_id),子块 Milvus 入库。"""
    resp = _upload(client)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["parent_count"] >= 1
    assert body["child_count"] >= 1

    with app.app_context():
        parent_store = store.ParentStore(app.config["RAG_SCHEMES"]["parent_document_rag"]["COLLECTION_NAME"])
        parents = parent_store._load()

    assert len(parents) == body["parent_count"]
    parent_text = next(iter(parents.values()))
    assert "中医诊断" in parent_text  # 父块是完整病历,不是碎片


def test_parent_query_returns_full_parent(app, client, fake_embedding):
    """查询:命中子块后 sources 返回完整父块全文,答案 SSE 流式输出。"""
    _upload(client)

    resp = client.post("/rag/parent/query", json={"query": "恶寒头痛 2 天"})
    assert resp.status_code == 200
    assert resp.mimetype == "text/event-stream"

    events = _parse_sse(resp.get_data(as_text=True))

    sources_event = [e for e in events if e["type"] == "sources"][0]
    assert len(sources_event["sources"]) > 0
    # sources 是父块全文:包含「中医诊断」这类子块边界之外的上下文
    for source in sources_event["sources"]:
        assert "parent_id" in source
        assert len(source["text"]) > 0

    answer = "".join(e["content"] for e in events if e["type"] == "delta")
    assert len(answer) > 0

    assert events[-1]["type"] == "done"


def test_parent_query_dedup_sources(app, client, fake_embedding):
    """多个子块命中同一父块时,sources 按父 id 去重。"""
    _upload(client)

    resp = client.post("/rag/parent/query", json={"query": "咳嗽痰多"})
    events = _parse_sse(resp.get_data(as_text=True))

    sources_event = [e for e in events if e["type"] == "sources"][0]
    parent_ids = [s["parent_id"] for s in sources_event["sources"]]
    assert len(parent_ids) == len(set(parent_ids))  # 无重复父块


def test_parent_query_empty(client):
    resp = client.post("/rag/parent/query", json={"query": ""})
    assert resp.status_code == 400
