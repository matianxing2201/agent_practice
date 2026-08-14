"""阶段 1:Indexing 索引——把知识库文档变成可检索的向量。

目标:让「任意文本片段」可以被「向量相似度」检索到。

关键步骤:
    1. 加载文档
       从文件/上传读取文本。先支持纯文本,后续可扩展 pdf/docx。
    2. 文本切分(chunking)
       长文档切成小块,记录每块的来源(文件名 + 位置)。
       参数见项目根 config.py:CHUNK_SIZE / CHUNK_OVERLAP。
    3. 向量化(embedding)
       用智谱 embedding-3 把每块文本转成向量,维度见 config.py:EMBEDDING_DIM。
    4. 写入 Milvus
       collection(见 config.py:RAG_SCHEMES)首次运行时自动创建
       (schema + 向量索引),批量写入向量与原文,
       每块存: 向量 | 原文 | 来源。

涉及概念:chunk 大小与重叠、embedding 维数、Milvus Collection/Schema/Index。

约定:本模块负责 collection 的创建与写入;检索阶段假设 collection 已存在。
"""
