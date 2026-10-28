"""Ollama SDK 常用方法。

    ollama.list()    列出本地磁盘已拉取的模型
    ollama.ps()      列出当前加载到内存中的运行模型
    ollama.show()    读取模型完整定义(参数 / 模板 / Modelfile)
    ollama.embed()   文本向量化
    ollama.create()  基于已有模型封装自定义模型
    ollama.delete()  删除本地模型
    ollama.pull()    从仓库拉取模型(stream=True 可显示进度)
"""

from . import controllers  # noqa: E402,F401
