"""案例② Neo4j 图数据库(前置知识)。

学习目标:理解属性图的节点 / 关系 / 属性 / Label,掌握 Cypher 的
CREATE / MERGE / MATCH / SET / DELETE 与关系遍历。

分层(与 rag 下其他方案同构):
    controllers.py  HTTP 路由(规划 URL 前缀 /rag/graph/neo4j)
    services.py     案例业务编排(连接状态 / 示例图 种子数据与查询 / 通用 Cypher)
    neo4j_store.py  图数据访问(neo4j-driver 5.x 客户端封装)

连接参数读 current_app.config(NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD,
定义于项目根 config.py;默认账号信息见 README)。

【TODO】待实现内容:
    - /status                驱动连通性 + 服务端版本
    - 示例图种子:Person 节点 + KNOWS 关系
    - 节点与关系查询:MATCH / 多跳遍历
    - 更新与删除:SET / DELETE
    - 通用 /cypher 执行口(便于学习者自测任意语句)
"""

from . import controllers  # noqa: E402,F401  注册案例路由到 rag bp
