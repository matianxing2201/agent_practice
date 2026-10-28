"""使用 Modelfile 中的模型配置创建自定义模型,并调用模型生成内容。"""

from ..client import get_client
from ..config import Conf

MODEL_NAME = "code-assistant"
SYSTEM_PROMPT = "你是一个专业Python代码助手，请根据用户需求写代码，仅输出代码与代码注释，其余内容全部舍弃不输出。"
MODEL_PARAMETERS = {
    "temperature": 0.2,
    "top_p": 0.8,
}


def create_model(model: str = MODEL_NAME) -> dict:
    """创建自定义模型,参数分别对应 Modelfile 的 FROM、SYSTEM 和 PARAMETER。"""
    response = get_client().create(
        model=model,
        from_=Conf.CHAT_MODEL,
        system=SYSTEM_PROMPT,
        parameters=MODEL_PARAMETERS,
    )
    return response.model_dump(mode="json")


def generate(prompt: str, model: str = MODEL_NAME) -> str:
    """使用自定义模型生成内容。"""
    response = get_client().generate(model=model, prompt=prompt)
    return response.response
