"""Hybrid RAG(混合检索 RAG)方案。

在 Naive RAG 的基础上改进检索阶段:向量语义化 + 关键词召回 + 重排序过滤噪声,
是企业落地最通用的检索方式。

与 naive_rag 的关系:
    同属 RAG 学习系列,共用同一套知识库(knowledge_base 模块)与生成阶段,
    差别只在 retrieval:
        naive_rag  单路向量检索,直接取 top_k
        hybrid_rag 两路混合:向量召回候选 -> BM25 关键词重排序 -> 取 top_k

    场景适配:
        适合:业务文档、合同、标书、规章制度等语义要求高的场景。
        不适合:逻辑推理要求高、知识库实体关系复杂严密的场景。

本方案内部按 controller / service 分层:

    controllers.py  HTTP 路由(注册到 rag 主题 bp,URL 前缀 /rag/hybrid)
    services.py     业务编排:controller 调用这里(混合检索 + 生成)
    retrieval.py    阶段 2 实现(向量召回 + BM25 重排序)
    generation.py   阶段 3 实现(与 naive_rag 同一生成模式)

配置(RAG_SCHEMES["hybrid_rag"]):
    COLLECTION_NAME  复用 tcm_medical_record 知识库
    CANDIDATE_K      向量召回候选数(默认 5,召回数 > 最终 TOP_K)
"""

from . import controllers  # noqa: E402,F401  注册本方案路由到 rag bp