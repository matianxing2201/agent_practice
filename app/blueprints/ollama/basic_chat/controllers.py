import json

from flask import Response, request, stream_with_context

from .. import bp
from . import services


@bp.route("/basic/chat", methods=["POST"])
def basic_chat():
    """基础对话:POST {"messages": [...], "options": {...}, "stream": false}。

    stream 为 true 时以 SSE 返回文本片段;否则返回完整 Ollama 响应。
    """
    data = request.get_json() or {}
    messages = data.get("messages", [])
    options = data.get("options")
    stream = data.get("stream", False)

    if not stream:
        return services.chat(messages, options)

    def events():
        for content in services.chat_stream(messages, options):
            yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(events()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
