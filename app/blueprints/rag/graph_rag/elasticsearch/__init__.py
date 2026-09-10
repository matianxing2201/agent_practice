"""案例① Elasticsearch + IK 中文检索(前置知识)。

学习目标:理解倒排索引、分词器对中文检索的决定性作用,以及
IK 的 ik_max_word(索引最细切分)与 ik_smart(查询智能切分)分工。

分层(与 rag 下其他方案同构):
    controllers.py  HTTP 路由(规划 URL 前缀 /rag/graph/es)
    services.py     案例业务编排(连通性 / 索引 / 写入 / 检索 / 分词演示)
    es_store.py     ES 数据访问(elasticsearch-py 8.x 客户端封装)

【TODO】待实现内容:
    - /status              连通性 + 集群信息
    - /analyze             IK 分词演示:ik_max_word vs ik_smart
    - 索引管理:创建带 IK mapping 的索引 / 删除索引
    - 文档写入:单条 / bulk 批量
    - 文档检索:match 中文查询 + 高亮
    - 复合查询:Bool / 分页
"""

from . import controllers  # noqa: E402,F401  注册案例路由到 rag bp
