"""Corrective-RAG 状态:工作流传递的状态快照。"""

from typing import TypedDict


class CRAGState(TypedDict):
    patient_desc: str  # 患者描述
    milvus_docs: list[str]  # Milvus 检索候选(未评审)
    relevant_docs: list[str]  # 评审后相关的病例(纠错后留下的)
    web_context: str  # 联网搜索补充的上下文(JSON 字符串)
    final_result: str  # 最终诊断