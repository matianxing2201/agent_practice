"""Ollama SDK 常用方法:模型管理和文本向量化。"""

from collections.abc import Iterator

from ..client import get_client
from ..config import Conf


def list_models() -> dict:
    """磁盘模型 list + 内存模型 ps。"""
    client = get_client()
    return {
        "installed": client.list().model_dump(mode="json"),
        "running": client.ps().model_dump(mode="json"),
    }


def show_model(model: str) -> dict:
    """查看模型完整定义。"""
    return get_client().show(model=model).model_dump(mode="json")


def embed(text: str) -> list[float]:
    """使用配置的向量模型将一段文本转换为向量。"""
    response = get_client().embed(model=Conf.EMBEDDING_MODEL, input=text)
    return list(response.embeddings[0])


def create_model(model: str, base_model: str | None = None, system: str | None = None) -> dict:
    """基于已有模型创建自定义模型。"""
    response = get_client().create(
        model=model,
        from_=base_model or Conf.CHAT_MODEL,
        system=system,
    )
    return response.model_dump(mode="json")


def delete_model(model: str) -> dict:
    """删除指定模型。"""
    return get_client().delete(model=model).model_dump(mode="json")


def pull_model(model: str) -> dict:
    """拉取模型,等待完成后返回状态。"""
    return get_client().pull(model=model).model_dump(mode="json")


def pull_model_stream(model: str) -> Iterator[dict]:
    """流式拉取模型,逐条返回进度。"""
    for progress in get_client().pull(model=model, stream=True):
        yield progress.model_dump(mode="json", exclude_none=True)
