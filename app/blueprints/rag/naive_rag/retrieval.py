"""
Retrieval 检索——从 Milvus 中找到与问题最相关的片段。

目标:给定用户问题,返回 top_k 个最相关的知识片段作为生成上下文。

关键步骤:
    1. 问题向量化
       必须使用与索引阶段相同的 embedding 模型,否则检索无意义。
    2. 相似度检索
       MilvusClient.search() 按向量相似度搜索,
       度量方式见项目根 config.py:METRIC_TYPE(COSINE / IP / L2)。
    3. 整理结果
       返回 top_k 片段:原文 + 相似度分 + 来源。
"""

from flask import current_app

from ..knowledge_base import services as kb_services
from ..knowledge_base.milvus_store import MilvusStore


def retrieve(query: str) -> list[dict]:
    """检索与问题最相关的知识片段。"""
    top_k = current_app.config["TOP_K"]

    query_vector = kb_services.embed_text(query)
    
    # 2. 相似度检索
    store = MilvusStore(
        current_app.config["RAG_SCHEMES"]["naive_rag"]["COLLECTION_NAME"]
    )
    store.ensure_collection()
    
    results = store.client.search(
        collection_name=store.collection_name,
        data=[query_vector],
        limit=top_k,
        output_fields=["text"],
    )
    
    # 3. 整理结果
    retrieved = []
    for result in results[0]:
        retrieved.append({
            "text": result["entity"]["text"],
            "score": result["distance"],
        })
    
    return retrieved
