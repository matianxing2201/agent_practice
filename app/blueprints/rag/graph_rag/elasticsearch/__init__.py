"""案例① Elasticsearch + IK 中文检索(前置知识)。

学习目标:理解倒排索引、分词器对中文检索的决定性作用,以及
IK 的 ik_max_word(写索引、切得最细)与 ik_smart(查询、智能切分)分工。

分层(与 rag 下其他方案同构):
    controllers.py  HTTP 路由(URL 前缀 /rag/graph/es,见文件头路由表)
    services.py     案例业务编排(连通性 / 索引 / 写入 / 检索 / 分词演示)
    es_store.py     ES 数据访问(elasticsearch-py 8.x 客户端封装)

访问顺序建议(也是课程 demo 的顺序):
    1. GET  /rag/graph/es/status                 先确认连得上、版本对不对
    2. POST /rag/graph/es/analyze                看 IK 到底怎么切中文
    3. POST /rag/graph/es/indexes                建 goods_v1(带 IK mapping)
    4. POST /rag/graph/es/indexes/goods_v1/docs  写几条商品(单条或 bulk)
    5. POST /rag/graph/es/indexes/goods_v1/search 中文检索 / bool 过滤 / 分页

"""

from . import controllers  # noqa: E402,F401  注册案例路由到 rag bp
