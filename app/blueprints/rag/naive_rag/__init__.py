"""Naive RAG(朴素 RAG)方案。

RAG = Retrieval-Augmented Generation(检索增强生成),解决 LLM 的两大缺陷:
幻觉(编造事实)和知识过时。思路:回答前先检索相关资料,让模型基于资料生成。

Naive RAG 是最基础的 RAG 流程,分三个阶段:

    1. Indexing(索引)     -> indexing.py
       知识库文档 -> 切分小块(chunk) -> 向量化(embedding) -> 存入 Milvus
    2. Retrieval(检索)    -> retrieval.py
       用户问题 -> 向量化 -> Milvus 相似度检索 -> 取回 top_k 相关片段
    3. Generation(生成)   -> generation.py
       「问题 + 检索片段」组装 prompt -> LLM -> 最终回答

本方案内部按 controller / service 分层:

    controllers.py  HTTP 路由(注册到 rag 主题 bp,URL 前缀 /rag/naive)
    services.py     业务编排:controller 调用这里,这里编排三个阶段
    indexing.py     阶段 1 实现
    retrieval.py    阶段 2 实现
    generation.py   阶段 3 实现

学习路径:
    按 indexing -> retrieval -> generation 顺序逐个填充,
    然后在 services.py 编排,最后在 controllers.py 注册路由。

技术要点:
    - Milvus 用新版 MilvusClient API(pymilvus 3.x,ORM 风格将在 3.1 移除)
    - 向量化用智谱 embedding-3,与后续检索必须用同一模型
    - 对话生成用 OpenCode Zen 的 deepseek-v4-flash(OpenAI 兼容接口)
    - 全部配置统一在项目根 config.py 管理
"""

from . import controllers  # noqa: E402,F401  注册本方案路由到 rag bp
