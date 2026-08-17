"""Naive RAG 业务编排。

answer_question_stream(...)   提问 -> retrieval.py 检索 -> generation.py 生成(流式)

知识库数据的索引与管理在 knowledge_base 模块(数据通过 /rag/knowledge/* 写入),
本方案是数据的使用者,不负责写入。
"""

import json

from . import retrieval, generation


def answer_question_stream(query: str):
    """流式回答:先发送检索到的 sources,再逐 chunk 发送生成内容。"""
    retrieved_docs = retrieval.retrieve(query)

    sources = [{"text": doc["text"], "score": doc["score"]} for doc in retrieved_docs]
    yield f"data: {json.dumps({'type': 'sources', 'sources': sources}, ensure_ascii=False)}\n\n"
    yield from generation.generate_answer_stream(query, retrieved_docs)
