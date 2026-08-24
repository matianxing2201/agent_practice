"""Self-RAG 方案:自省 RAG + 工作流。

普通 RAG 是「无条件检索 -> 生成」;Self-RAG 让 LLM 对检索动作和检索结果
做元判断:要不要检索(judge)、查得对不对(filter)、够不够用(check)、
不够就重检索,直到资料充足再生成。参考 5_self_rag(LangGraph StateGraph)。

检索复用共享知识库 tcm_medical_record(与 naive/hybrid/agentic 同库),
方案内只新增「自省控制流」——这正是本方案区别于其他 RAG 的教学核心。
"""

from .. import bp
from . import controllers  # noqa: F401  导入即注册路由到 rag 蓝图