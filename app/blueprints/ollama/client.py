"""Ollama 客户端:专题内所有案例共用。

"""

import ollama

from .config import Conf


def get_client() -> ollama.Client:
    """按专题配置创建 Ollama 客户端。"""
    return ollama.Client(host=Conf.HOST)
