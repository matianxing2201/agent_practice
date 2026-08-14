"""阶段 2:Retrieval 检索——从 Milvus 中找到与问题最相关的片段。

目标:给定用户问题,返回 top_k 个最相关的知识片段作为生成上下文。

关键步骤:
    1. 问题向量化
       必须使用与索引阶段相同的 embedding 模型,否则检索无意义。
    2. 相似度检索
       MilvusClient.search() 按向量相似度搜索,
       度量方式见项目根 config.py:METRIC_TYPE(COSINE / IP / L2)。
    3. 整理结果
       返回 top_k 片段:原文 + 相似度分 + 来源。

涉及概念:相似度度量、top_k、向量搜索参数(limit)。

前置条件:collection 已由索引阶段创建并写入数据。
"""
