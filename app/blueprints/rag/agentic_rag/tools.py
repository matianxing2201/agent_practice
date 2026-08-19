"""Agentic RAG 工具层:LangChain @tool 工具对象。

search_local_tool   本地知识库检索(向量化 -> Milvus top_k)
search_online_tool  联网搜索(Tavily)

@tool 装饰器根据函数签名 + docstring 自动生成工具 schema
(名称/描述/参数),LangChain Agent(langchain.agents.create_agent)
据此让 LLM 自主决定是否调用、传什么参数。


"""

import json

from flask import current_app
from langchain_core.tools import tool

from ..knowledge_base import services as kb_services
from ..knowledge_base.milvus_store import MilvusStore


@tool("search_local_tool")
def search_local(query: str) -> str:
    """搜索本地中医病历知识库,检索与给定症状描述相似的病历记录。返回 JSON 数组字符串。"""
    scheme = current_app.config["RAG_SCHEMES"]["agentic_rag"]
    top_k = scheme["TOP_K"]

    query_vector = kb_services.embed_text(query)
    store = MilvusStore(scheme["COLLECTION_NAME"])
    store.ensure_collection()

    results = store.client.search(
        collection_name=store.collection_name,
        data=[query_vector],
        limit=top_k,
        output_fields=["text"],
    )
    docs = [
        {"text": r["entity"]["text"], "score": r["distance"]}
        for r in results[0]
    ]
    return json.dumps(docs, ensure_ascii=False)


@tool("search_online_tool")
def search_online(query: str) -> str:
    """联网搜索相关知识,获取本地知识库之外的最新信息。返回 JSON 数组字符串。"""
    from tavily import TavilyClient

    client = TavilyClient(api_key=current_app.config["TAVILY_API_KEY"])
    resp = client.search(query=query, search_depth="advanced", max_results=5)
    return json.dumps(resp.get("results", []), ensure_ascii=False)
