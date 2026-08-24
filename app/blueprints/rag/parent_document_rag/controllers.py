from flask import Response, jsonify, request, stream_with_context

from .. import bp
from . import services


@bp.route("/parent/upload", methods=["POST"])
def parent_upload():
    file = request.files.get("file")
    if file is None or not file.filename.lower().endswith(".txt"):
        return {"error": "只支持 .txt 文件"}, 400

    content = file.read().decode("utf-8")
    if not content.strip():
        return {"error": "文件内容为空"}, 400

    return jsonify(services.create_vector_data(content))


@bp.route("/parent/query", methods=["POST"])
def parent_query():
    data = request.get_json(silent=True) or {}
    query_text = data.get("query", "").strip()

    if not query_text:
        return {"error": "query 不能为空"}, 400

    return Response(
        stream_with_context(services.answer_question_stream(query_text)),
        mimetype="text/event-stream",
    )

