"""Graph RAG 学习主题:前置知识案例容器。

正式实现 Graph RAG 之前,先补齐两个底层知识点:

    elasticsearch/   案例① 中文检索基础设施:ES + IK 分词器(已实现)
    neo4j/           案例② 图数据库基础设施:Cypher / 节点关系(待实现)

每个案例内部按 controller / service / store 三层组织(与 rag 下其他
方案同构),后续 Graph RAG 主体可直接复用这两个子包的 store 层。
"""

# 两个案例各自 import 自己的 controllers,把路由注册到上层 rag bp
from . import elasticsearch  # noqa: E402,F401

# 【TODO】neo4j 案例实现后放开,并同步在 rag/__init__.py 中注册本模块
from . import neo4j  # noqa: E402,F401
