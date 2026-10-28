import json

from flask import Response, request, stream_with_context

from .. import bp
from . import services


@bp.route("/methods/models", methods=["GET"])
def list_models():
    """查看本地已安装模型和当前运行模型。"""
    return services.list_models()


@bp.route("/methods/models/<path:model>", methods=["GET"])
def show_model(model: str):
    """查看指定模型的详细信息。"""
    return services.show_model(model)


@bp.route("/methods/embed", methods=["POST"])
def embed_text():
    """文本向量化:POST {"input": "..."}。"""
    data = request.get_json() or {}
    return {"embedding": services.embed(data.get("input", ""))}


@bp.route("/methods/models/create", methods=["POST"])
def create_model():
    """创建模型:POST {"model": "...", "from": "...", "system": "..."}。"""
    data = request.get_json() or {}
    return services.create_model(
        model=data.get("model", ""),
        base_model=data.get("from"),
        system=data.get("system"),
    )


@bp.route("/methods/models/<path:model>", methods=["DELETE"])
def delete_model(model: str):
    """删除指定模型。"""
    return services.delete_model(model)


@bp.route("/methods/models/pull", methods=["POST"])
def pull_model():
    """拉取模型:POST {"model": "...", "stream": false}。"""
    data = request.get_json() or {}
    model = data.get("model", "")

    if not data.get("stream", False):
        return services.pull_model(model)

    def events():
        for progress in services.pull_model_stream(model):
            yield f"data: {json.dumps(progress, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(events()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
