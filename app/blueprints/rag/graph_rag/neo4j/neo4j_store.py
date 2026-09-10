"""Neo4j 数据访问层:neo4j-driver 5.x 客户端封装。

连接参数读 current_app.config(NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD,
定义于项目根 config.py),对应 docker-compose.elastic-neo4j.yml 的 neo4j 服务。

【TODO】待实现:
    Neo4jStore 类:driver 连接与关闭 / verify_connectivity /
                  run_cypher(返回 [{...}] 记录列表)

占位骨架,待实现。
"""
