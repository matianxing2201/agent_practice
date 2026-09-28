"""Neo4j 案例:业务编排层。

controllers 调这里,把课程中的示例图(Person-KNOWS 认识关系)的
建图 / 查询 / 清理组织成可复现的步骤;真正的 Cypher 在 neo4j_store 层。

已实现:
    create_person   创建 Person 节点(CREATE 不幂等)
    upsert_person   合并 Person 节点(MERGE 幂等:有则更新,无则创建)
    find_persons    查询 Person 节点(全量 / 按 name / 按 min_age 过滤)
    create_relationship  在两个已存在的 Person 间建立 KNOWS 关系(MERGE 幂等)
    find_relationships   查询 KNOWS 关系(全量 / 只查某人作为起点认识的)
    update_person       按 name 更新 Person 的 age / city(SET)
    delete_person       按 name 删除 Person 节点(DETACH DELETE,连相关关系一起删)

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


def create_relationship(p1_name: str, p2_name: str, since: int) -> dict:
    """在两个已存在的 Person 之间建立 KNOWS 关系,返回关系信息。

    MATCH 两个已有节点后 MERGE 关系(p1)-[:KNOWS]->(p2)。
    since 是关系属性,记录认识年份。MERGE 关系幂等:同对节点不重复建边,
    但 since 会按传入值更新(`ON CREATE/ON MATCH` 双分支,类似 upsert_person)。

    注意如果 p1 或 p2 不存在,MATCH 匹配不到节点,不会建边。
    """
    store = _store()
    try:
        rows = store.run_cypher(
            "MATCH (p1:Person {name: $p1_name}), (p2:Person {name: $p2_name}) "
            "MERGE (p1)-[r:KNOWS {since: $since}]->(p2) "
            "ON CREATE SET r.since = $since "
            "ON MATCH SET r.since = $since "
            "RETURN p1, r, p2",
            params={"p1_name": p1_name, "p2_name": p2_name, "since": since},
        )
        if not rows:
            return {"created": False, "reason": "一端或两端 Person 不存在"}
        rel = rows[0]["r"]
        return {
            "p1": rows[0]["p1"].get("name"),
            "p2": rows[0]["p2"].get("name"),
            "type": rel.type,
            "since": rel.get("since"),
        }
    finally:
        store.close()


def find_relationships(from_name: str = None) -> list:
    """查询 KNOWS 关系列表。

    from_name 为空         MATCH 所有 (p1)-[:KNOWS]-(p2) 无向关系
    from_name 有值         查"此人作为起点认识的人" -> (p1)-[:KNOWS]->(p2) 有向

    返回每条的 from / to / since,便于展示社交关系。
    """
    if from_name:
        cypher = (
            "MATCH (p:Person {name: $from_name})-[r:KNOWS]->(o:Person) "
            "RETURN p.name AS from_name, r.since AS since, o.name AS to_name"
        )
        params = {"from_name": from_name}
    else:
        cypher = (
            "MATCH (p1:Person)-[r:KNOWS]-(p2:Person) "
            "RETURN p1.name AS from_name, r.since AS since, p2.name AS to_name"
        )
        params = {}

    store = _store()
    try:
        rows = store.run_cypher(cypher, params=params)
        return [dict(rec) for rec in rows]
    finally:
        store.close()


def update_person(name: str, age: int = None, city: str = None) -> dict:
    """按 name 更新 Person 的属性并返回更新后的节点。

    SET 更新 age / city。name 是定位键,不会变。
    若 name 不存在,MATCH 匹配不到,rows 为空 -> 返回 {"updated": False}。
    """
    assignments = []
    params = {"name": name}
    if age is not None:
        assignments.append("p.age = $age")
        params["age"] = age
    if city:
        assignments.append("p.city = $city")
        params["city"] = city

    if not assignments:
        return {"updated": False, "reason": "没有可更新的字段(age / city 至少给一个)"}

    cypher = f"MATCH (p:Person {{name: $name}}) SET {', '.join(assignments)} RETURN p"

    store = _store()
    try:
        rows = store.run_cypher(cypher, params=params)
        if not rows:
            return {"updated": False, "reason": f"Person {name} 不存在"}
        node = rows[0]["p"]
        return {"updated": True, "name": node.get("name"), "age": node.get("age"), "city": node.get("city")}
    finally:
        store.close()


def delete_person(name: str) -> dict:
    """按 name 删除 Person 节点,返回删除的数量。

    用 DETACH DELETE:连节点带它所有关联关系一并删除。
    若不 detach,节点仍有关系时 DELETE 会报错;detach 是图库删节点的常见做法。
    returns: {"deleted": 条数}。0 表示该 name 不存在。
    """
    store = _store()
    try:
        rows = store.run_cypher(
            "MATCH (p:Person {name: $name}) DETACH DELETE p "
            "RETURN count(p) AS c",
            params={"name": name},
        )
        deleted = rows[0]["c"] if rows else 0
        return {"deleted": deleted}
    finally:
        store.close()