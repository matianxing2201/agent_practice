"""Naive RAG(朴素 RAG)方案。

RAG = Retrieval-Augmented Generation(检索增强生成),解决 LLM 的两大缺陷:
幻觉(编造事实)和知识过时。思路:回答前先检索相关资料,让模型基于资料生成。

Naive RAG 是最基础的 RAG 流程,分三个阶段,本方案负责后两个:

    1. Indexing(索引)     -> knowledge_base 模块负责
       知识库文档 -> 切分小块(chunk) -> 向量化(embedding) -> 存入 Milvus
       数据写入走 /rag/knowledge/*(upload 上传 txt / 手动录入)
    2. Retrieval(检索)    -> retrieval.py
       用户问题 -> 向量化 -> Milvus 相似度检索 -> 取回 top_k 相关片段
    3. Generation(生成)   -> generation.py
       「问题 + 检索片段」组装 prompt -> LLM -> 最终回答

Milvus 访问与向量化复用 knowledge_base 模块(MilvusStore / embed_text),
本方案是数据的使用者,不重复实现索引与存储,只做检索、生成的领域逻辑。

本方案内部按 controller / service 分层:

    controllers.py  HTTP 路由(注册到 rag 主题 bp,URL 前缀 /rag/naive)
    services.py     业务编排:controller 调用这里(检索 + 生成)
    retrieval.py    阶段 2 实现
    generation.py   阶段 3 实现

技术要点:
    - Milvus 用新版 MilvusClient API(pymilvus 3.x),复用 knowledge_base.milvus_store
    - 向量化用智谱 embedding-3(knowledge_base.services.embed_text),与检索必须用同一模型
    - 对话生成用 OpenCode Zen 的 deepseek-v4-flash(OpenAI 兼容接口)
    - 全部配置统一在项目根 config.py 管理
"""

from . import controllers  # noqa: E402,F401  注册本方案路由到 rag bp
