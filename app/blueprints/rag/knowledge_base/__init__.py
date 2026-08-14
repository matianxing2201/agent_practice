"""知识库管理模块(独立于具体 RAG 方案)。

职责:管理 Milvus 中的知识库数据(中医病历),提供 CRUD。
naive_rag 等方案是数据的使用者,本模块是数据的管理者。

结构:
    controllers.py    HTTP 路由(/rag/knowledge/*)
    services.py       业务编排(分割、向量化、读写编排)
    milvus_store.py   Milvus 数据访问
"""

from . import controllers  # noqa: E402,F401  注册路由到 rag bp
