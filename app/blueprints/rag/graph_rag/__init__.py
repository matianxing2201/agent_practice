"""Graph RAG 学习主题:前置知识案例容器。

正式实现 Graph RAG 之前,先补齐两个底层知识点(与课程
big-model/6_AIAgent/AIAgentStudy/7_graph_rag/ 对应):

    elasticsearch/   案例① 中文检索基础设施:ES + IK 分词器
    neo4j/           案例② 图数据库基础设施:Cypher / 节点关系

每个案例内部按 controller / service / store 三层组织(与 rag 下其他
方案同构),后续 Graph RAG 主体可直接复用这两个子包的 store 层。

【TODO】两案例实现完成后,再在 rag/__init__.py 中注册本模块。
"""

# 占位:案例实现就绪后取消注释(各 controllers 会把路由注册到 rag bp)
# from . import elasticsearch  # noqa: E402,F401
# from . import neo4j  # noqa: E402,F401
