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
