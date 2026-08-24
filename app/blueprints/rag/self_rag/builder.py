"""Self-RAG 工作流组装:LangGraph StateGraph 状态机。"""

from langgraph.constants import END, START
from langgraph.graph import StateGraph

from .nodes import (
    node_check_sufficiency,
    node_filter_docs,
    node_generate,
    node_judge_retrieve,
    node_retrieve,
    route_judge,
    route_sufficiency,
)
from .state import SelfRAGState


def build_workflow():
    """把 5 个节点 + 2 个条件路由组装成可编译的图。"""
    graph = StateGraph(SelfRAGState)

    graph.add_node("judge_retrieve", node_judge_retrieve)
    graph.add_node("retrieve", node_retrieve)
    graph.add_node("filter_docs", node_filter_docs)
    graph.add_node("check_sufficiency", node_check_sufficiency)
    graph.add_node("generate", node_generate)

    graph.add_edge(START, "judge_retrieve")
    graph.add_conditional_edges(
        source="judge_retrieve",
        path=route_judge,
        path_map={"end": END, "retrieve": "retrieve"},
    )
    graph.add_edge("retrieve", "filter_docs")
    graph.add_edge("filter_docs", "check_sufficiency")
    graph.add_conditional_edges(
        source="check_sufficiency",
        path=route_sufficiency,
        path_map={"retrieve": "retrieve", "generate": "generate"},
    )
    graph.add_edge("generate", END)

    return graph.compile()