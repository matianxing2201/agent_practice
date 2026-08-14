"""知识库 CRUD 的 HTTP seam 测试。"""

import io


def test_upload_file_splits_cases(client, fake_embedding):
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

    data = client.get("/rag/knowledge").get_json()
    assert data["total"] == 2
    texts = [item["text"] for item in data["items"]]
    assert any(t.startswith("1 感冒") for t in texts)
    assert any(t.startswith("2 咳嗽") for t in texts)


def test_upload_rejects_non_txt(client):
    resp = client.post(
        "/rag/knowledge/upload",
        data={"file": (io.BytesIO(b"content"), "doc.pdf")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400


def test_list_empty(client):
    resp = client.get("/rag/knowledge")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 0
    assert data["items"] == []


def test_create_empty_text_400(client):
    resp = client.post("/rag/knowledge", json={"text": "   "})
    assert resp.status_code == 400


def test_create_manual_record(client, fake_embedding):
    resp = client.post(
        "/rag/knowledge", json={"text": "1 感冒・风寒束表证\n主诉:恶寒头痛 2 天"}
    )
    assert resp.status_code == 201
    record_id = resp.get_json()["id"]
    assert isinstance(record_id, int)

    data = client.get("/rag/knowledge").get_json()
    assert data["total"] == 1
    assert data["items"][0]["text"].startswith("1 感冒")


def test_get_record_detail(client, fake_embedding):
    created = client.post(
        "/rag/knowledge", json={"text": "感冒・风热犯表证\n主诉:发热咽痛"}
    ).get_json()
    record_id = created["id"]

    resp = client.get(f"/rag/knowledge/{record_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["id"] == record_id
    assert data["text"].startswith("感冒・风热犯表证")


def test_get_missing_record_404(client):
    resp = client.get("/rag/knowledge/999999")
    assert resp.status_code == 404


def test_update_record_keeps_id_and_reembeds(client, fake_embedding):
    created = client.post(
        "/rag/knowledge", json={"text": "旧文本内容"}
    ).get_json()
    record_id = created["id"]
    calls_before = fake_embedding.calls["n"]

    resp = client.put(f"/rag/knowledge/{record_id}", json={"text": "新文本内容"})
    assert resp.status_code == 200
    assert fake_embedding.calls["n"] == calls_before + 1  # 确认重新向量化

    data = client.get(f"/rag/knowledge/{record_id}").get_json()
    assert data["id"] == record_id  # id 不变
    assert data["text"] == "新文本内容"


def test_update_missing_record_404(client):
    resp = client.put("/rag/knowledge/999999", json={"text": "任意文本"})
    assert resp.status_code == 404


def test_delete_record(client, fake_embedding):
    record_id = client.post(
        "/rag/knowledge", json={"text": "待删除记录"}
    ).get_json()["id"]

    resp = client.delete(f"/rag/knowledge/{record_id}")
    assert resp.status_code == 204

    assert client.get(f"/rag/knowledge/{record_id}").status_code == 404
    assert client.get("/rag/knowledge").get_json()["total"] == 0


def test_delete_missing_record_404(client):
    resp = client.delete("/rag/knowledge/999999")
    assert resp.status_code == 404
