"""Controller 层:Naive RAG 的 HTTP 路由。

路由注册到 rag 主题的 blueprint(bp),URL 带 /naive/ 前缀:

    GET  /rag/naive            方案概览
    POST /rag/naive/documents  上传文档,触发索引(indexing)
    POST /rag/naive/query      提问,触发检索 + 生成(retrieval -> generation)

职责:只处理请求/响应(解析参数、调用 services、返回 JSON),
不写业务逻辑——业务编排在 services.py。
"""

from flask import jsonify

from .. import bp
from . import services


@bp.route("/naive", methods=["GET"])
def overview():
    """方案概览(链路测试:GET /rag/naive)。"""
    return jsonify(services.get_overview())
