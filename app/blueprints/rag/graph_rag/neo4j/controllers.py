"""Neo4j 案例:HTTP 路由(注册到 rag 主题 blueprint)。

规划 URL 前缀 /rag/graph/neo4j(注册到 .. 的 rag bp)。

【TODO】实现以下路由(具体见 __init__.py 的学习目标):
    GET  /rag/graph/neo4j/status
    POST /rag/graph/neo4j/demo/seed     示例图种子(Person + KNOWS,幂等)
    GET  /rag/graph/neo4j/demo/graph    读取示例关系图
    POST /rag/graph/neo4j/cypher        通用 Cypher 执行

占位骨架,待实现。
"""

# from flask import jsonify, request
# from .. import bp
# from . import services
