"""知识库管理模块:CRUD 业务编排。

Controller 调用这里的函数,这里负责:文本分割、向量化、Milvus 读写编排。
向量化(embed_text)调用智谱 embedding API,是外部依赖边界(测试可替换)。
"""

import re

from flask import current_app

from .milvus_store import MilvusStore

# 病例编号行,如 "1 感冒・风寒束表证"(每条病例的分割点)
_CASE_START = re.compile(r"^\d+\s")


def _store() -> MilvusStore:
    collection_name = current_app.config["RAG_SCHEMES"]["naive_rag"]["COLLECTION_NAME"]
    return MilvusStore(collection_name)


def embed_text(text: str) -> list[float]:
    """文本向量化(智谱 embedding-3,外部依赖边界)。"""
    from openai import OpenAI

    client = OpenAI(
        api_key=current_app.config["EMBEDDING_API_KEY"],
        base_url=current_app.config["EMBEDDING_BASE_URL"],
    )
    resp = client.embeddings.create(
        model=current_app.config["EMBEDDING_MODEL"],
        input=text,
        dimensions=current_app.config["EMBEDDING_DIM"],
    )
    return resp.data[0].embedding


def split_cases(content: str) -> list[str]:
    """按编号行(如 "1 感冒・...")把 txt 分割成独立病例。"""
    cases: list[str] = []
    current: list[str] = []
    for line in content.strip().splitlines():
        if _CASE_START.match(line):
            if current:
                cases.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        cases.append("\n".join(current))
    return cases


def import_file(content: str) -> int:
    """批量导入:分割病例 -> 逐条向量化 -> 批量入库,返回条数。"""
    cases = split_cases(content)
    vectors = [embed_text(case) for case in cases]
    _store().insert(cases, vectors)
    return len(cases)


def create_record(text: str) -> int:
    """手动输入单条:向量化后入库,返回自增 id。"""
    vector = embed_text(text)
    ids = _store().insert([text], [vector])
    return ids[0]


def get_record(record_id: int) -> dict | None:
    """按 id 查单条记录。"""
    return _store().get(record_id)


def update_record(record_id: int, text: str) -> bool:
    """按 id 更新 text(自动重新向量化,id 不变)。记录不存在返回 False。"""
    store = _store()
    if store.get(record_id) is None:
        return False
    vector = embed_text(text)
    return store.update(record_id, text, vector)


def delete_record(record_id: int) -> bool:
    """按 id 删除记录。记录不存在返回 False。"""
    return _store().delete(record_id)


def list_records(page: int, size: int) -> dict:
    """分页列表。"""
    items, total = _store().list_records(page, size)
    return {"items": items, "total": total, "page": page, "size": size}
