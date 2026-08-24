"""Self-RAG 业务编排:运行工作流,返回自省结果。"""

from flask import current_app

from .builder import build_workflow


def answer_question(query: str) -> dict:
    """运行 Self-RAG 工作流,返回 {answer, sources, retrieve_round}。

    answer          最终诊断(或提示语)
    sources         自省过滤后实际使用的有效病例块
    retrieve_round  自省轮数(>1 说明发生了「资料不足→重检索」)
    """
    workflow = build_workflow()
    state = workflow.invoke(
        {
            "patient_msg": query,
            "medical_record_list": [],
            "valid_medical_record_list": [],
            "final_result": None,
            "retrieve_round": 0,
        }
    )
    return {
        "answer": state["final_result"],
        "sources": state["valid_medical_record_list"],
        "retrieve_round": state["retrieve_round"],
    }