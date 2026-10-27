"""案2:多轮对话与补全。

对话(Chat Completion):
    输入 messages 列表,必须带 role(system / user / assistant),
    多轮历史全部传入,模型才能"记住"上下文。

补全(Completion):
    输入一整段 prompt 文本,没有角色划分,模型只负责续写。

两者底层是同一套模型逻辑,只是调用参数不同:
    ollama.chat(...)      messages 列表
    ollama.generate(...)  prompt 字符串
"""

from . import controllers  # noqa: E402,F401
