"""Neo4j 案例:业务编排层。

controllers 调这里,把课程中的示例图(Person-KNOWS 认识关系)的
建图 / 查询 / 清理组织成可复现的步骤;真正的 Cypher 在 neo4j_store 层。

已实现:
    create_person   创建 Person 节点(CREATE 不幂等)
    upsert_person   合并 Person 节点(MERGE 幂等:有则更新,无则创建)
    find_persons    查询 Person 节点(全量 / 按 name / 按 min_age 过滤)

规划待实现:
    status / seed_demo_graph / fetch_demo_graph / run_cypher / reset_demo_graph
"""

from flask import current_app

from .neo4j_store import Neo4jStore


def _store() -> Neo4jStore:
    return Neo4jStore()


def create_person(name: str, age: int) -> dict:
    """创建单个 Person 节点,返回创建的节点。

    cypher 里的 $name / $age 是参数化占位,值通过 params 传入,
    不要格式化进字符串 —— 既能防注入,也是驱动对 Cypher 的规范用法。
    """
    store = _store()
    try:
        rows = store.run_cypher(
            "CREATE (p:Person {name: $name, age: $age}) RETURN p",
            params={"name": name, "age": age},
        )
        node = rows[0]["p"] if rows else {}
        return {"name": node.get("name"), "age": node.get("age"), "element_id": node.element_id}
    finally:
        store.close()


def upsert_person(name: str, age: int) -> dict:
    """按 name 合并 Person 节点,返回节点(MERGE 幂等)。

    和 create_person(CREATE)的区别:
        CREATE   每次调都新建一条,重复调用会产出多个同名节点
        MERGE    以 name 作为匹配键,有则 ON MATCH 更新,无则 ON CREATE 创建
                 —— 所以重复调用不会产生重复节点,适合做幂等种子数据。
    """
    store = _store()
    try:
        rows = store.run_cypher(
            "MERGE (p:Person {name: $name}) "
            "ON CREATE SET p.age = $age "
            "ON MATCH SET p.age = $age "
            "RETURN p",
            params={"name": name, "age": age},
        )
        node = rows[0]["p"] if rows else {}
        return {"name": node.get("name"), "age": node.get("age"), "element_id": node.element_id}
    finally:
        store.close()


def find_persons(name: str = None, min_age: int = None) -> list:
    """查询 Person 节点列表。

    三种筛选场景:
        都不传          MATCH 所有人
        传 min_age      WHERE p.age >= $min_age 过滤
        传 name         按 name 精确匹配

    WHERE 子句按需拼接,name / min_age 可组合(用 AND 连接)。
    注意 cypher 语句是字面量 + 条件追加,动态值仍走 params,不字符串化。
    """
    conditions = []
    params = {}

    if name:
        conditions.append("p.name = $name")
        params["name"] = name
    if min_age is not None:
        conditions.append("p.age >= $min_age")
        params["min_age"] = min_age

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    cypher = f"MATCH (p:Person) {where_clause} RETURN p ORDER BY p.name"

    store = _store()
    try:
        rows = store.run_cypher(cypher, params=params)
        return [
            {"name": rec["p"].get("name"), "age": rec["p"].get("age"), "element_id": rec["p"].element_id}
            for rec in rows
        ]
    finally:
        store.close()