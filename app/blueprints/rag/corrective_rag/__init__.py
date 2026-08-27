"""Corrective-RAG 方案:纠错 RAG。

普通 RAG 检索完直接生成;CRAG 在中间加一道「相关性评审」关卡——
检索结果逐条评审,相关的留下,不足 MIN_RELEVANT_DATA_COUNT 条就
放弃本地内容、转 Tavily 联网搜索补充,避免拿不相关检索结果硬编答案。


"""

from .. import bp
from . import controllers  # noqa: F401  导入即注册路由到 rag 蓝图