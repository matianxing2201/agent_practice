"""Corrective-RAG 工作流组装:LangGraph StateGraph。"""

from langgraph.constants import END, START
from langgraph.graph import StateGraph

from .nodes import (
    node_generate_answer,
    node_grade_milvus_docs,
    node_milvus_search,
    node_web_search,
    route_decide_to_generate_answer,
)
from .state import CRAGState


def build_workflow():
    graph = StateGraph(CRAGState)

    graph.add_node("milvus_search", node_milvus_search)
    graph.add_node("grade_milvus_docs", node_grade_milvus_docs)
    graph.add_node("web_search", node_web_search)
    graph.add_node("generate_answer", node_generate_answer)

    graph.add_edge(START, "milvus_search")
    graph.add_edge("milvus_search", "grade_milvus_docs")
    graph.add_conditional_edges(
        source="grade_milvus_docs",
        path=route_decide_to_generate_answer,
        path_map={
            "web_search": "web_search",
            "generate_answer": "generate_answer",
        },
    )
    graph.add_edge("web_search", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()