"""
    Neo4j 医学方剂 HTTP 路由。
    POST   /rag/graph/neo4j/medicine/seed         读 data/ JSON 全量建图
    POST   /rag/graph/neo4j/medicine              建单个中药(关联分类)
    POST   /rag/graph/neo4j/medicine/prescription      建单个方剂(关联类型+组成)
    GET    /rag/graph/neo4j/medicine/prescription      按名称查方剂信息+组成
"""

from flask import jsonify, request

from .... import bp  # 4个点:medicine_prescription -> neo4j -> graph_rag -> rag(定义 bp)
from . import services


@bp.route("/graph/neo4j/medicine/seed", methods=["POST"])
def medicine_seed_graph():
    """读子包 data/ 下 medicine.json / prescription.json,全量构造图谱。

    幂等:内部全部 MERGE,重复调用不会产生重复数据。返回导入统计。
    """
    result = services.seed_graph()
    return jsonify(result), 201


@bp.route("/graph/neo4j/medicine", methods=["POST"])
def medicine_create_medicine():
    """创建 / 合并单个中药节点,并关联到中药分类。
    body 需包含中药全部属性:name / chapter / section / nature_flavor /
    meridian / application / dosage / caution
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not (data.get("name") or "").strip():
        return jsonify({"error": "body 必须是对象,且 name 不能为空"}), 400

    services.create_medicine(data)
    return jsonify({"created": data["name"].strip()}), 201


@bp.route("/graph/neo4j/medicine/prescription", methods=["POST"])
def medicine_create_prescription():
    """创建 / 合并单个方剂节点,并关联方剂类型与组成中药。
    body 需包含方剂全部属性:name / unit / subunit / function /
    indication / compatibility_meaning / compatibility_feature / usage / other
    composition: [{drug: 中药名}, ...]
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not (data.get("name") or "").strip():
        return jsonify({"error": "body 必须是对象,且 name 不能为空"}), 400

    services.create_prescription(data)
    return jsonify({"created": data["name"].strip()}), 201


@bp.route("/graph/neo4j/medicine/prescription", methods=["GET"])
def medicine_search_prescription():
    """按方剂名查询:方剂信息 + 组成中药列表。
    query 参数:
        name   方剂名称(必填),如 ?name=柴胡疏肝散
    """
    name = (request.args.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name 不能为空"}), 400

    return jsonify(services.search_prescription(name))