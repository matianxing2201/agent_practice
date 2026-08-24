"""测试基础设施。

- app fixture:testing 环境 + 独立测试 collection(不污染真实 tcm_medical_record)
- client fixture:HTTP seam(test_client)
- embedding 替身:替换智谱 API 调用,返回确定性向量
"""

import hashlib
from pathlib import Path

import pytest

from app import create_app

# 独立测试 collection,与真实知识库隔离
TEST_COLLECTION = "tcm_medical_record_test"
TEST_COLLECTION_PD = "tcm_medical_record_pd_test"


@pytest.fixture
def app():
    application = create_app("testing")
    application.config["RAG_SCHEMES"] = {
        "naive_rag": {"COLLECTION_NAME": TEST_COLLECTION},
        "hybrid_rag": {
            "COLLECTION_NAME": TEST_COLLECTION,
            "CANDIDATE_K": 5,
        },
        "agentic_rag": {
            "COLLECTION_NAME": TEST_COLLECTION,
            "TOP_K": 3,
            "MAX_ITERATIONS": 5,
        },
        "parent_document_rag": {
            "COLLECTION_NAME": TEST_COLLECTION_PD,
            "PARENT_CHUNK_SIZE": 800,
            "PARENT_CHUNK_OVERLAP": 100,
            "CHILD_CHUNK_SIZE": 300,
            "CHILD_CHUNK_OVERLAP": 50,
            "TOP_K": 3,
        },
        "self_rag": {
            "COLLECTION_NAME": TEST_COLLECTION,
            "TOP_K": 3,
            "MAX_RETRIEVE_ROUND": 3,
        },
    }
    application.config["TAVILY_API_KEY"] = "test-tavily-key"
    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_collection(app):
    """每个测试前清空测试数据,保证测试相互隔离:Milvus collection + 父块 JSON 文件。"""

    def _drop():
        from pymilvus import MilvusClient

        with app.app_context():
            uri = (
                f"http://{app.config['MILVUS_HOST']}:{app.config['MILVUS_PORT']}"
            )
            client = MilvusClient(uri=uri)
            for coll in (TEST_COLLECTION, TEST_COLLECTION_PD):
                if client.has_collection(coll):
                    client.drop_collection(coll)
            parent_file = Path(app.config["KNOWLEDGE_BASE_DIR"]) / f"parent_chunks_{TEST_COLLECTION_PD}.json"
            parent_file.unlink(missing_ok=True)

    _drop()
    yield
    _drop()


@pytest.fixture
def fake_embedding(monkeypatch):
    """替换 knowledge_base.services.embed_text:返回确定性 2048 维向量,并记录调用次数。

    naive_rag 的 retrieval 也通过 kb_services.embed_text 调用,因此同样生效。
    """

    from app.blueprints.rag.knowledge_base import services

    calls = {"n": 0}

    def fake_embed(text: str) -> list[float]:
        calls["n"] += 1
        seed = hashlib.md5(text.encode("utf-8")).hexdigest()
        base = [int(seed[i : i + 2], 16) / 255 for i in range(0, 32, 2)]
        return (base * 128)[:2048]

    monkeypatch.setattr(services, "embed_text", fake_embed)
    fake_embed.calls = calls
    return fake_embed
