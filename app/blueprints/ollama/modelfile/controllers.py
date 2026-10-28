from flask import request

from .. import bp
from . import services


@bp.route("/modelfile/create", methods=["POST"])
def create_model():
    """创建自定义模型:POST {"model": "code-assistant"}。"""
    data = request.get_json() or {}
    model = data.get("model", "code-assistant")
    return services.create_model(model)


@bp.route("/modelfile/generate", methods=["POST"])
def generate():
    """使用自定义模型生成内容:POST {"prompt": "..."}。"""
    data = request.get_json() or {}
    prompt = data.get("prompt", "")
    model = data.get("model", services.MODEL_NAME)
    return {"response": services.generate(prompt, model)}
