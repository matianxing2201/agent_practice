"""
职责:只处理 HTTP 请求/响应——解析参数、调用 Service、返回 JSON。
不写业务逻辑,业务逻辑在 services.py。
"""

from flask import jsonify

from . import bp
from .services import get_rag_overview


@bp.route("/", methods=["GET"])
def index():
    """RAG 主题入口:返回主题概览。

    访问: GET /rag/
    """
    return jsonify(get_rag_overview())
