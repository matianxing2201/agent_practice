from flask import jsonify, request

from .. import bp
from . import services


@bp.route("/rag/query", methods=["POST"])
def rag_query():
    """RAG 问答:POST {"query": "发烧,头痛,流鼻涕"}。"""
    data = request.get_json(silent=True) or {}
    result = services.answer_question(data.get("query", ""))
    return jsonify(result)
