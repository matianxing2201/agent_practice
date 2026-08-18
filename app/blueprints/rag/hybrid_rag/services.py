"""
answer_question_stream(...)   提问 -> retrieval.py 混合检索 -> generation.py 生成(流式)

与 naive_rag 的区别只在检索阶段:
    naive_rag  仅向量相似度检索,直接取 top_k
    hybrid_rag 向量召回候选 + BM25 关键词重排序过滤噪声
"""

import json

from . import retrieval, generation


def answer_question_stream(query: str):
    """混合检索:向量召回候选 -> BM25 重排序 -> 返回最终 top_k 片段。"""
    retrieved_docs = retrieval.retrieve(query)

    sources = [{"text": doc["text"], "score": doc["score"]} for doc in retrieved_docs]
    yield f"data: {json.dumps({'type': 'sources', 'sources': sources}, ensure_ascii=False)}\n\n"
    yield from generation.generate_answer_stream(query, retrieved_docs)