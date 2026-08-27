"""Self-RAG 工作流节点:每个节点是状态机里的一步,路由决定分支走向。

参考 5_self_rag 的 workflow,流程:
    judge_retrieve(要不要检索?) ──DIRECT→ 结束
              │RETRIEVE
              ▼
    retrieve → filter_docs(逐块过滤) → check_sufficiency(够不够?)
                                            │ENOUGH
              ┌─────────────────────────────┤
              └─LACK(重检索)                ▼
                                          generate → 结束

Self-RAG 与普通 RAG 的区别:检索动作和检索结果都要经过 LLM 自省——
「要不要查、查得对不对、够不够用」。
"""

from flask import current_app
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from ..knowledge_base import services as kb_services
from ..knowledge_base.milvus_store import MilvusStore
from . import prompts
from .state import SelfRAGState


def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=current_app.config["CHAT_API_KEY"],
        base_url=current_app.config["CHAT_BASE_URL"],
        model=current_app.config["CHAT_MODEL"],
        temperature=0.7,
    )


def _invoke(template, **variables) -> str:
    """用 prompt 调 LLM,返回纯文本结果"""
    return (template | _llm() | StrOutputParser()).invoke(variables)


def _retrieve(patient_msg: str) -> list[str]:
    """向量检索共享知识库,返回 top_k 个备选病例块文本。"""
    scheme = current_app.config["RAG_SCHEMES"]["self_rag"]
    store = MilvusStore(scheme["COLLECTION_NAME"])
    store.ensure_collection()
    results = store.client.search(
        collection_name=store.collection_name,
        data=[kb_services.embed_text(patient_msg)],
        limit=scheme["TOP_K"],
        output_fields=["text"],
    )
    return [r["entity"]["text"] for r in results[0]]


# ---- 节点 1:自省「要不要检索」 ----
def node_judge_retrieve(state: SelfRAGState) -> SelfRAGState:
    result = _invoke(prompts.judge_retrieve_template, patient_msg=state["patient_msg"])
    if result == "DIRECT":
        # 闲聊/无关:不检索,直接给提示
        state["final_result"] = "请输入与中西医相关的描述，便于我给出中医诊断与治疗方案"
    return state


def route_judge(state: SelfRAGState) -> str:
    """judge 节点路由:已有最终结果(闲聊)则结束,否则进入检索。"""
    return "end" if state.get("final_result") is not None else "retrieve"


# ---- 节点 2:检索,生成备选数据 ----
def node_retrieve(state: SelfRAGState) -> SelfRAGState:
    state["medical_record_list"] = _retrieve(state["patient_msg"])
    state["valid_medical_record_list"] = []
    state["retrieve_round"] += 1
    return state


# ---- 节点 3:逐块自省过滤,只留有效数据 ----
def node_filter_docs(state: SelfRAGState) -> SelfRAGState:
    for chunk in state["medical_record_list"]:
        result = _invoke(
            prompts.filter_docs_template,
            patient_msg=state["patient_msg"],
            doc_chunk=chunk[:1500],
        ).strip()
        if result == "YES":
            state["valid_medical_record_list"].append(chunk)
    return state


# ---- 节点 4:自省「有效数据够不够」 ----
def node_check_sufficiency(state: SelfRAGState) -> SelfRAGState:
    if not state["valid_medical_record_list"]:
        return state  # 没有有效数据,交给路由决定

    result = _invoke(
        prompts.check_sufficiency_template,
        patient_msg=state["patient_msg"],
        valid_medical_record_list=state["valid_medical_record_list"],
    ).strip()
    scheme = current_app.config["RAG_SCHEMES"]["self_rag"]
    if result == "LACK" and state["retrieve_round"] < scheme["MAX_RETRIEVE_ROUND"]:
        # 资料不够且还有重试机会:清空备选/有效,回到 retrieve 再来一轮
        state["medical_record_list"] = []
        state["valid_medical_record_list"] = []
    return state


def route_sufficiency(state: SelfRAGState) -> str:
    """check 节点路由:被清空(要重检索)则回到 retrieve,否则生成。"""
    if not state["medical_record_list"] and state["retrieve_round"] < current_app.config["RAG_SCHEMES"]["self_rag"]["MAX_RETRIEVE_ROUND"]:
        return "retrieve"
    return "generate"


# ---- 节点 5:生成最终答案 ----
def node_generate(state: SelfRAGState) -> SelfRAGState:
    if not state["valid_medical_record_list"]:
        # 过滤后没有可用资料:直接给提示,不调生成 LLM(修正参考的死代码)
        state["final_result"] = "暂无可参考的病例资料，无法做出辩证论治方案"
        return state

    result = _invoke(
        prompts.generate_template,
        patient_msg=state["patient_msg"],
        medical_record="".join(state["valid_medical_record_list"]),
    )
    state["final_result"] = result
    return state