"""Parent-Document RAG 业务编排。

入库(索引侧,本方案自包含):
    create_vector_data  文档 -> 父子两级切分 -> 父块存 JSON 文件 + 子块存 Milvus
    为什么索引放在方案内而非 knowledge_base:父子索引正是本方案的教学主题,
    knowledge_base 保持「单层 CRUD」的纯粹,不被第二套 schema 入侵;
    这里只复用 kb_services.embed_text(向量化组件)。

查询(检索侧):
    answer_question_stream  子块向量检索 -> 父 id 集合(去重)-> 父块全文
        -> SSE:先发 sources(命中的父块全文),再流式输出 LLM 答案(delta)
    链路演示「小块找得准、大块读得全」:命中的是小块的向量,回传的是大块的全文。
"""

import json
import uuid

from flask import current_app
from langchain_openai import ChatOpenAI

from ..knowledge_base import services as kb_services
from . import prompts
from .splitter import split_parent_child
from .store import ChildStore, ParentStore


def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=current_app.config["CHAT_API_KEY"],
        base_url=current_app.config["CHAT_BASE_URL"],
        model=current_app.config["CHAT_MODEL"],
        temperature=0.7,
    )


def _scheme() -> dict:
    return current_app.config["RAG_SCHEMES"]["parent_document_rag"]


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def create_vector_data(doc_content: str) -> dict:
    """入库:父块写 JSON 文件,子块(带父 id 指针)写 Milvus。返回块数统计。"""
    scheme = _scheme()
    pairs = split_parent_child(
        doc_content,
        scheme["PARENT_CHUNK_SIZE"],
        scheme["PARENT_CHUNK_OVERLAP"],
        scheme["CHILD_CHUNK_SIZE"],
        scheme["CHILD_CHUNK_OVERLAP"],
    )

    parents: dict[str, str] = {}
    child_rows: list[dict] = []
    for p_text, child_texts in pairs:
        parent_id = str(uuid.uuid4())
        parents[parent_id] = p_text
        for child_text in child_texts:
            child_rows.append(
                {
                    "text": child_text,
                    "vector": kb_services.embed_text(child_text),
                    "parent_id": parent_id,
                }
            )

    ParentStore(scheme["COLLECTION_NAME"]).save_many(parents)
    child_count = ChildStore(scheme["COLLECTION_NAME"]).insert_children(child_rows)
    return {"parent_count": len(parents), "child_count": child_count}


def answer_question_stream(query: str):
    """流式回答:先发 sources(命中的父块全文),再逐块流式生成答案(SSE)。"""
    scheme = _scheme()

    hits = ChildStore(scheme["COLLECTION_NAME"]).search(
        kb_services.embed_text(query), scheme["TOP_K"]
    )
    # 多个子块可能命中同一父块,按父 id 去重且保持命中顺序
    parent_ids = list(dict.fromkeys(h["parent_id"] for h in hits))
    sources = ParentStore(scheme["COLLECTION_NAME"]).get_many(parent_ids)

    yield _sse({"type": "sources", "sources": sources})

    medical_record = "\n\n".join(s["text"] for s in sources)
    messages = [
        {"role": "system", "content": prompts.SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"----用户症状----\n{query}\n\n----中医病例记录----\n{medical_record}",
        },
    ]
    for chunk in _llm().stream(messages):
        if getattr(chunk, "content", None):
            yield _sse({"type": "delta", "content": chunk.content})
    yield _sse({"type": "done"})

