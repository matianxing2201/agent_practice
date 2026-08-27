"""Corrective-RAG 工作流节点:检索 -> 评审 -> (相关够?生成 / 不够?联网) -> 生成。

普通 RAG 检索完直接生成;CRAG 多一道「相关性评审」关卡——
relevant_docs 不足 MIN_RELEVANT_DATA_COUNT 就放弃本地内容、转联网搜索,
避免 LLM 拿不相关检索结果硬编答案(纠错的核心)。

"""

import json

from flask import current_app
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from ..knowledge_base import services as kb_services
from ..knowledge_base.milvus_store import MilvusStore
from . import prompts
from .state import CRAGState


def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=current_app.config["CHAT_API_KEY"],
        base_url=current_app.config["CHAT_BASE_URL"],
        model=current_app.config["CHAT_MODEL"],
        temperature=0.7,
    )


def _invoke(template, **variables) -> str:
    """用 prompt 调 LLM,返回纯文本结果。"""
    return (template | _llm() | StrOutputParser()).invoke(variables)


def _scheme() -> dict:
    return current_app.config["RAG_SCHEMES"]["corrective_rag"]


def _search_knowledge_base(query_vector: list[float], top_k: int) -> list[str]:
    """检索共享知识库,返回 top_k 个候选文本。"""
    scheme = _scheme()
    store = MilvusStore(scheme["COLLECTION_NAME"])
    store.ensure_collection()
    results = store.client.search(
        collection_name=store.collection_name,
        data=[query_vector],
        limit=top_k,
        output_fields=["text"],
    )
    return [r["entity"]["text"] for r in results[0]]


# ---- 节点 1:检索知识库 ----
def node_milvus_search(state: CRAGState) -> CRAGState:
    state["milvus_docs"] = _search_knowledge_base(
        kb_services.embed_text(state["patient_desc"]), _scheme()["RETRIEVE_TOP_K"]
    )
    return state


# ---- 节点 2:逐条评审相关性,留下相关的 ----
def node_grade_milvus_docs(state: CRAGState) -> CRAGState:
    if not state["milvus_docs"]:
        return state  # 无候选可评审,relevant 保持空,路由会走联网

    for chunk in state["milvus_docs"]:
        result = _invoke(
            prompts.grade_milvus_docs_template,
            patient_desc=state["patient_desc"],
            docs_chunk=chunk,
        ).strip()
        if result == "relevant":
            state["relevant_docs"].append(chunk)  # 存病例内容,不是评审标记(修正参考 bug)


# ---- 路由:相关资料够就直接生成,不够就联网纠错 ----
def route_decide_to_generate_answer(state: CRAGState) -> str:
    if len(state["relevant_docs"]) >= _scheme()["MIN_RELEVANT_DATA_COUNT"]:
        return "generate_answer"
    return "web_search"


# ---- 节点 3:联网搜索补充(纠错路径) ----
def node_web_search(state: CRAGState) -> CRAGState:
    from tavily import TavilyClient

    client = TavilyClient(api_key=current_app.config["TAVILY_API_KEY"])
    resp = client.search(
        query=state["patient_desc"],
        search_depth="advanced",
        max_results=_scheme()["SEARCH_MAX_RESULTS"],
    )
    state["web_context"] = json.dumps(resp.get("results", []), ensure_ascii=False)
    return state


# ---- 节点 4:生成最终诊断 ----
def node_generate_answer(state: CRAGState) -> CRAGState:
    state["final_result"] = _invoke(
        prompts.generate_answer_template,
        patient_desc=state["patient_desc"],
        relevant_docs=state["relevant_docs"],
        web_context=state["web_context"] or "无",
    )
    return state