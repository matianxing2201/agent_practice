"""Neo4j 数据访问层:neo4j-driver 5.x 客户端封装。

连接参数读 current_app.config(NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD,
定义于项目根 config.py),对应 docker-compose.elastic-neo4j.yml 的 neo4j 服务。
"""

from typing import cast, LiteralString

from flask import current_app
from neo4j import GraphDatabase, Result


class Neo4jStore:
    """封装对 Neo4j 的连接,以及通用 Cypher 执行。

    初始化建 driver、close 关 driver、
    run_cypher 在会话里执行语句。所有查询统一走 run_cypher 入口。
    """

    def __init__(self):
        """建立驱动,连接参数从 config 读取。"""
        self.driver = GraphDatabase.driver(
            current_app.config["NEO4J_URI"],
            auth=(
                current_app.config["NEO4J_USER"],
                current_app.config["NEO4J_PASSWORD"],
            ),
        )

    def close(self) -> None:
        """关闭驱动,释放连接池。"""
        if self.driver:
            self.driver.close()

    def run_cypher(self, cypher: str, params: dict | None = None) -> list[dict]:
        """执行一条 Cypher,返回记录字典列表。

        params 是参数化查询的占位参数(如 {name: "张三"}),可以防注入,
        别把值直接格式化进 cypher 字符串里。
        """
        params = params or {}
        with self.driver.session() as sess:
            _cypher = cast(LiteralString, cypher)  # 仅类型标记,运行时无副作用
            res: Result = sess.run(_cypher, params)
            return [rec.data() for rec in res]


