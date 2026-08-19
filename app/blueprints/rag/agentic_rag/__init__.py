"""Agentic RAG 方案:LLM 自主决策的检索增强生成。

与 naive/hybrid 的区别:检索不再是固定的「先检索再生成」管线,
而是把「检索」封装成工具,交给 LLM 自主决策——
要不要查本地、要不要联网、查几次(子查询),直到信息足够再回答。

参考 3_agentic_rag,使用 LangChain Agent 框架:
    @tool 工具对象(tools.py)+ langchain.agents.create_agent(services.py),
    循环控制由框架负责,agent.invoke() 一次性跑完,
    我们遍历最终消息列表,把过程映射为 JSON 返回(trace/sources/answer)。
"""

from .. import bp
from . import controllers  # noqa: F401  导入即注册路由到 rag 蓝图
