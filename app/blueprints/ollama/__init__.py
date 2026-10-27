"""Ollama 学习主题:本地大模型工具。

    1. basic_chat             基础对话与参数配置(temperature / top_p / num_predict)
    2. multi_chat_completion  多轮对话与补全(chat vs generate)
    3. common_methods         SDK 常用方法:list / ps / show / create / delete / pull / embed
    4. modelfile              自定义模型:Modelfile -> ollama create
    5. rag                    RAG:切分 -> 向量化 -> ChromaDB -> 检索生成
    6. function_calling       工具调用:calculator 示例
    7. http_service           Ollama 原生 HTTP API(/api/chat)与流式转发
    8. vision                 多模态:LLaVA 图片理解
    9. model_concept          模型概念:参数 / 量化 / 上下文窗口 / Dense-MoE
    10. chat_models           通用对话模型选型
    11. other_models          推理 / 代码 / 多模态 / 嵌入模型选型

"""

from flask import Blueprint

bp = Blueprint("ollama", __name__, url_prefix="/ollama")

from . import basic_chat  # noqa: E402,F401
from . import multi_chat_completion  # noqa: E402,F401
