"""1:基础对话与参数配置。

要点:
    - ollama.chat 一次性返回 vs stream=True 流式返回
    - options 常用参数:
        temperature  越小越确定(专业场景 0.1~0.4,创意场景 0.7~1.0)
        top_p        候选词概率累积阈值(0~1,越小越保守)
        num_predict  最大输出 token 数
"""

from . import controllers  # noqa: E402,F401
