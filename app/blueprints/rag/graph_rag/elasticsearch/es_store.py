"""Elasticsearch 数据访问层:elasticsearch-py 8.x 客户端封装。

连接参数读 current_app.config(ES_HOST / ES_PORT,定义于项目根 config.py),
索引默认名读 RAG_SCHEMES["graph_rag"]["ES_INDEX"]。

【TODO】待实现:
    EsStore 类:ping / info / ensure_index(IK mapping) / delete_index /
               bulk_insert / search(IK match + highlight) / analyze(IK 分词)

占位骨架,待实现。
"""
