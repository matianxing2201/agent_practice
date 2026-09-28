"""Neo4j 案例:HTTP 路由(注册到 rag 主题 blueprint)。

规划 URL 前缀 /rag/graph/neo4j(注册到 .. 的 rag bp)。

    POST /rag/graph/neo4j/demo/person   创建 Person 节点

规划 TODO(见 __init__.py 的学习目标):
    GET  /rag/graph/neo4j/status
    POST /rag/graph/neo4j/demo/seed     示例图种子(Person + KNOWS,幂等)
    GET  /rag/graph/neo4j/demo/graph    读取示例关系图
    POST /rag/graph/neo4j/cypher        通用 Cypher 执行
"""

from flask import jsonify, request

from ... import bp  # 三个点:neo4j 嵌在 graph_rag 下,往上两层才是 rag(那里定义了 bp)
from . import services


@bp.route("/graph/neo4j/demo/person", methods=["POST"])
def neo4j_create_person():
    """创建 Person 节点。body: {"name": "张三", "age": 18}"""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name 不能为空"}), 400

    age = data.get("age")
    if not isinstance(age, int) or age < 0:
        return jsonify({"error": "age 要是非负整数"}), 400

    return jsonify(services.create_person(name, age)), 201


@bp.route("/graph/neo4j/demo/person/merge", methods=["POST"])
def neo4j_upsert_person():
    """合并 Person 节点。body: {"name": "张三", "age": 20}

    以 name 为键 MERGE:节点不存在则创建,已存在则更新 age,幂等。
    """
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name 不能为空"}), 400

    age = data.get("age")
    if not isinstance(age, int) or age < 0:
        return jsonify({"error": "age 要是非负整数"}), 400

    return jsonify(services.upsert_person(name, age)), 200


@bp.route("/graph/neo4j/demo/persons", methods=["GET"])
def neo4j_find_persons():
    """查询 Person 节点。query 参数(都可选):
        name      按 name 精确匹配
        min_age   只返回 age >= min_age 的节点
    都不传则返回全部 Person。
    """
    name = (request.args.get("name") or "").strip() or None

    min_age_raw = request.args.get("min_age")
    min_age = None
    if min_age_raw not in (None, ""):
        try:
            min_age = int(min_age_raw)
        except ValueError:
            return jsonify({"error": "min_age 要是整数"}), 400
        if min_age < 0:
            return jsonify({"error": "min_age 不能为负"}), 400

    return jsonify(services.find_persons(name=name, min_age=min_age))


@bp.route("/graph/neo4j/demo/relationship", methods=["POST"])
def neo4j_create_relationship():
    """在两个已存在的 Person 间建立 KNOWS 关系。
    body: {"p1_name": "张三", "p2_name": "李四", "since": 2025}
    """
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "body 必须是对象"}), 400

    p1_name = (data.get("p1_name") or "").strip()
    p2_name = (data.get("p2_name") or "").strip()
    if not p1_name or not p2_name:
        return jsonify({"error": "p1_name / p2_name 不能为空"}), 400
    if p1_name == p2_name:
        return jsonify({"error": "p1_name 和 p2_name 不能相同"}), 400

    since = data.get("since")
    if not isinstance(since, int) or isinstance(since, bool):
        return jsonify({"error": "since 必须是整数(认识年份)"}), 400

    return jsonify(services.create_relationship(p1_name, p2_name, since))


@bp.route("/graph/neo4j/demo/relationships", methods=["GET"])
def neo4j_find_relationships():
    """查询 KNOWS 关系。query 参数:
        from_name   可选。传了只查"此人作为起点认识的人";
                    不传则返回所有 KNOWS 关系(无向)。
    """
    from_name = (request.args.get("from_name") or "").strip() or None
    return jsonify(services.find_relationships(from_name=from_name))


@bp.route("/graph/neo4j/demo/person/update", methods=["POST"])
def neo4j_update_person():
    """按 name 更新 Person 属性。
    body: {"name": "小明", "age": 18, "city": "北京"}(age / city 至少给一个)
    """
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "body 必须是对象"}), 400

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name 不能为空"}), 400

    age = data.get("age")
    if age is not None and (not isinstance(age, int) or isinstance(age, bool)):
        return jsonify({"error": "age 必须是整数"}), 400

    city = (data.get("city") or "").strip() or None

    return jsonify(services.update_person(name, age=age, city=city))


@bp.route("/graph/neo4j/demo/person", methods=["DELETE"])
def neo4j_delete_person():
    """按 name 删除 Person 节点。
    body: {"name": "张三"}(DETACH DELETE,相关关系一并删)
    """
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "body 必须是对象"}), 400

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name 不能为空"}), 400

    return jsonify(services.delete_person(name))
