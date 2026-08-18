"""
Hybrid RAG 检索——向量召回 + BM25 关键词重排序。

目标:先用向量语义召回候选片段(召回候选数 > 最终返回数),
再用 BM25 关键词相关性重排序,过滤掉语义相似但关键词不相关的噪声,
取最终 top_k 作为生成上下文。

参考 2_hybrid_rag 方案:
    向量语义化 + 关键词召回 + 重排序过滤噪声,企业落地最通用的方式。

关键步骤:
    1. 向量召回
       问题向量化 -> Milvus 相似度检索,取 CANDIDATE_K 条候选。
    2. BM25 关键词重排序
       对候选文本 jieba 分词建立 BM25 索引 -> 对用户输入分词打分
       -> 按分数降序取 TOP_K 条。BM25 是词频统计模型,擅长关键词匹配,
       可过滤向量检索中"语义近但字面无关"的噪声。
"""

import jieba
from flask import current_app
from rank_bm25 import BM25Okapi

from ..knowledge_base import services as kb_services
from ..knowledge_base.milvus_store import MilvusStore


def _vector_recall(query: str) -> list[dict]:
    """阶段 1:向量召回候选片段(召回数 > 最终返回数)。"""
    candidate_k = current_app.config["RAG_SCHEMES"]["hybrid_rag"]["CANDIDATE_K"]

    query_vector = kb_services.embed_text(query)

    store = MilvusStore(
        current_app.config["RAG_SCHEMES"]["hybrid_rag"]["COLLECTION_NAME"]
    )
    store.ensure_collection()

    results = store.client.search(
        collection_name=store.collection_name,
        data=[query_vector],
        limit=candidate_k,
        output_fields=["text"],
    )

    return [
        {"text": r["entity"]["text"], "vector_score": r["distance"]}
        for r in results[0]
    ]


def _bm25_rerank(query: str, candidates: list[dict]) -> list[dict]:
    """阶段 2:BM25 关键词重排序,返回最终 top_k。

    为什么向量召回后还要用 BM25 重排:
        Milvus 向量检索衡量「语义相似度」,语义近不代表字面相关——
        比如问"恶寒头痛",可能与"咳嗽痰多"的病历语义空间很近,
        但关键词零重合,对回答毫无帮助,属于噪声。
        而 BM25 是词频统计模型,衡量「关键词重合度」:
        用户原话中的词是否真的出现在文本里。
        因此:
            向量召回(宽)保证语义相关的都捞进候选池,宁多勿漏;
            BM25 重排(窄)只留字面真正相关的,过滤语义噪声。
        两者是互补的两段式检索(candidate generation + re-ranking)。
    """
    top_k = current_app.config["TOP_K"]

    # 知识库为空时无候选可排序
    if not candidates:
        return []

    # 候选文本 jieba 分词,构建 BM25 索引
    token_corpus = [jieba.lcut(c["text"]) for c in candidates]
    bm25 = BM25Okapi(token_corpus)

    # 用户输入分词,得到各候选的 BM25 分数
    query_tokens = jieba.lcut(query)
    scores = bm25.get_scores(query_tokens)

    # 按分数降序取 top_k(候选不足 top_k 时取全部)
    idxes = scores.argsort()[-top_k:][::-1]
    return [
        {"text": candidates[idx]["text"], "score": float(scores[idx])}
        for idx in idxes
    ]


def retrieve(query: str) -> list[dict]:
    candidates = _vector_recall(query)
    return _bm25_rerank(query, candidates)
