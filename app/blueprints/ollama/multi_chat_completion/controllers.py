from flask import request

from .. import bp
from . import services


@bp.route("/multi/chat", methods=["POST"])
def multi_chat():
    """多轮对话:POST {"messages": [...]}。每次请求传入完整历史消息。"""
    data = request.get_json() or {}
    messages = data.get("messages", [])
    return services.chat(messages)


@bp.route("/multi/completion", methods=["POST"])
def multi_completion():
    """文本补全:POST {"prompt": "..."}。"""
    data = request.get_json() or {}
    prompt = data.get("prompt", "")
    return {"response": services.completion(prompt)}
