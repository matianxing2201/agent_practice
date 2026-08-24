"""Self-RAG 状态:工作流在节点间传递的状态快照。"""

from typing import TypedDict


class SelfRAGState(TypedDict):
    patient_msg: str  # 患者描述
    medical_record_list: list[str]  # 备选病例块(检索原始结果)
    valid_medical_record_list: list[str]  # 有效病例块(自省过滤后)
    final_result: str | None  # 最终诊断
    retrieve_round: int  # 自省轮数(配合 MAX_RETRIEVE_ROUND 防死循环)