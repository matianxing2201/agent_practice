"""基础对话服务:封装 Ollama SDK 的普通与流式聊天调用。"""

from collections.abc import Iterator

from ..client import get_client
from ..config import Conf


def _options(options: dict | None = None) -> dict:
    """使用专题默认采样参数,并允许请求覆盖单项配置。"""
    configured = {
        "temperature": Conf.TEMPERATURE,
        "top_p": Conf.TOP_P,
        "num_predict": Conf.NUM_PREDICT,
    }
    if options:
        configured.update(options)
    return configured


def chat(messages: list, options: dict | None = None) -> dict:
    """一次性对话,返回完整响应。"""
    response = get_client().chat(
        model=Conf.CHAT_MODEL,
        messages=messages,
        options=_options(options),
    )
    return response.model_dump()


def chat_stream(messages: list, options: dict | None = None) -> Iterator[str]:
    """流式对话,逐 chunk 产出模型生成的文本。"""
    stream: Iterator = get_client().chat(
        model=Conf.CHAT_MODEL,
        messages=messages,
        options=_options(options),
        stream=True,
    )
    for chunk in stream:
        content = chunk.message.content
        if content:
            yield content
