"""多轮对话与文本补全服务。"""

from ..client import get_client
from ..config import Conf


def chat(messages: list) -> dict:
    """多轮对话:传入完整 messages 历史。"""
    response = get_client().chat(
        model=Conf.CHAT_MODEL,
        messages=messages,
    )
    return response.model_dump()


def completion(prompt: str) -> str:
    """补全:对一段文本续写。"""
    response = get_client().generate(
        model=Conf.CHAT_MODEL,
        prompt=prompt,
    )
    return response.response
