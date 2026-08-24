from flask import jsonify, request

from .. import bp
from . import services


@bp.route("/self/query", methods=["POST"])
def self_query():
    data = request.get_json(silent=True) or {}
    query_text = data.get("query", "").strip()

    if not query_text:
        return {"error": "query 不能为空"}, 400

    return jsonify(services.answer_question(query_text))