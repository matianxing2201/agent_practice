"""Corrective-RAG 业务编排。

与 self_rag 的区别:
    self_rag      自省「检索动作」——要不要查、查得对不对、够不够用(多轮重检索)
    corrective    评审「检索结果」——相关才留,不相关放弃,不够就联网补(一次性纠错)

输出:SSE 流式(参考代码把最终答案逐字符流式输出)。
"""

import json

from .builder import build_workflow


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def answer_question_stream(patient_desc: str):
    """运行 CRAG 工作流,把最终答案逐块流式输出(SSE)。"""
    workflow = build_workflow()
    state = workflow.invoke(
        {
            "patient_desc": patient_desc,
            "milvus_docs": [],
            "relevant_docs": [],
            "web_context": "",
            "final_result": "",
        }
    )
    answer = state["final_result"]
    # 逐块输出(参考代码逐字符,这里按块,减少事件数量)
    for piece in [answer[i : i + 20] for i in range(0, len(answer), 20)]:
        yield _sse({"content": piece})
    yield _sse({"done": True})