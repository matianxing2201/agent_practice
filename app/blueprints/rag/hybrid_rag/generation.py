"""阶段 3:Generation 生成——LLM 基于混合检索结果回答。

与 naive_rag 同一套生成模式:系统提示(中医医师,只依据资料回答)
+ 检索片段上下文 + 用户问题,组装 prompt 后流式调用 LLM。

区别只在前置检索:本方案的 retrieved_docs 来自 hybrid_rag/retrieval.py
(向量召回 + BM25 重排序),而非朴素向量检索。
"""

import json

from flask import current_app


def _build_messages(query: str, retrieved_docs: list[dict]) -> list[dict]:
    system_prompt = """你是一个中医医师，你需要根据患者的症状与中医病例记录作出中医诊断。
    请只依据提供的资料回答，不要编造信息。如果资料中没有相关信息，请明确说明。"""

    context_parts = []
    for i, doc in enumerate(retrieved_docs, 1):
        context_parts.append(f"病例记录 {i}:\n{doc['text']}")
    context = "\n\n".join(context_parts)

    user_prompt = f"""----用户输入的症状信息----
    {query}
    ----中医病例记录----
    {context}
    """
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _openai_client():
    from openai import OpenAI

    return OpenAI(
        api_key=current_app.config["CHAT_API_KEY"],
        base_url=current_app.config["CHAT_BASE_URL"],
    )


def generate_answer_stream(query: str, retrieved_docs: list[dict]):
    """流式生成:逐 chunk yield SSE 格式字符串。"""
    messages = _build_messages(query, retrieved_docs)
    client = _openai_client()

    stream = client.chat.completions.create(
        model=current_app.config["CHAT_MODEL"],
        messages=messages,
        temperature=0.7,
        stream=True,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield f"data: {json.dumps({'type': 'delta', 'content': chunk.choices[0].delta.content}, ensure_ascii=False)}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"