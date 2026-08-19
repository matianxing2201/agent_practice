"""RAG 学习主题:蓝图容器。

本层只定义主题蓝图,不再承担 controller/service 职责——每个 RAG 方案
(如 naive_rag)内部自行分层。方案的路由注册到本 bp,URL 前缀 /rag。
"""

from flask import Blueprint

# url_prefix:本主题所有路由都挂在 /rag 下
bp = Blueprint("rag", __name__, url_prefix="/rag")

# 导入方案与模块,让其中的 controllers 把路由注册到本蓝图
from . import knowledge_base  # noqa: E402,F401
from . import naive_rag  # noqa: E402,F401
from . import hybrid_rag  # noqa: E402,F401
from . import agentic_rag  # noqa: E402,F401
