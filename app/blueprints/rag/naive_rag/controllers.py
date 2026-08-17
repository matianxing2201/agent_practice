from flask import Response, request, stream_with_context

from .. import bp
from . import services


@bp.route("/naive/query", methods=["POST"])
def query():
    data = request.get_json(silent=True) or {}
    query_text = data.get("query", "").strip()

    if not query_text:
        return {"error": "query 不能为空"}, 400

    return Response(
        stream_with_context(services.answer_question_stream(query_text)),
        mimetype="text/event-stream",
    )
