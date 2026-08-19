"""Agentic RAG 业务编排:LangChain Agent + JSON 返回。

与 naive/hybrid 的区别:检索不再是固定的「先检索再生成」管线,
而是交给 LLM 自主决策——要不要调用工具、调用哪个、调用几次(子查询)。

本方案使用 LangChain Agent 框架(与参考 3_agentic_rag 同思路):
    @tool 工具对象(tools.py)+ langchain.agents.create_agent ——
    工具 schema 生成、调用分发、消息回填、循环控制全部由框架负责。
    agent.invoke() 一次性跑完整个 ReAct 循环,返回完整状态。

返回 JSON(一次性,非流式):
    trace   「决策 -> 观察」过程(教学可见性,玻璃盒)
    sources 循环中检索到的本地知识片段
    answer  最终答案(最后一条无工具调用的 AI 消息)
"""

import json

from flask import current_app
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.errors import GraphRecursionError

from . import prompts, tools


def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=current_app.config["CHAT_API_KEY"],
        base_url=current_app.config["CHAT_BASE_URL"],
        model=current_app.config["CHAT_MODEL"],
        temperature=0.7,
    )


def answer_question(user_input: str) -> dict:
    """Agent 跑完整个 ReAct 循环,返回 {trace, sources, answer}。"""
    scheme = current_app.config["RAG_SCHEMES"]["agentic_rag"]
    agent = create_agent(
        _llm(),
        [tools.search_local, tools.search_online],
        system_prompt=prompts.SYSTEM_PROMPT,
    )
    # 每次 ReAct 迭代 = model 节点 + tools 节点两步,再加 2 步余量
    recursion_limit = scheme["MAX_ITERATIONS"] * 2 + 2

    trace_events: list[dict] = []
    local_docs: list[dict] = []
    final_content = ""
    try:
        state = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config={"recursion_limit": recursion_limit},
        )
        for message in state["messages"]:
            if isinstance(message, AIMessage) and message.tool_calls:
                # 决策:LLM 决定调用工具(可能一次多个)
                for call in message.tool_calls:
                    trace_events.append(
                        {
                            "phase": "decide",
                            "tool": call["name"],
                            "args": call.get("args", {}),
                            "message": f"决定调用 {call['name']},参数 {call.get('args', {})}",
                        }
                    )
            elif isinstance(message, ToolMessage):
                # 观察:工具执行结果
                summary = str(message.content)[:100]
                trace_events.append(
                    {
                        "phase": "observe",
                        "tool": message.name,
                        "message": f"{message.name} 返回:{summary}",
                    }
                )
                if message.name == "search_local_tool" and isinstance(message.content, str):
                    try:
                        local_docs.extend(json.loads(message.content))
                    except (json.JSONDecodeError, TypeError):
                        pass
            elif isinstance(message, AIMessage):
                # 无工具调用的 AI 消息 = 最终答案(最后一条覆盖)
                if isinstance(message.content, str):
                    final_content = message.content
    except GraphRecursionError:
        trace_events.append(
            {
                "phase": "limit",
                "message": f"已达最大迭代次数 {scheme['MAX_ITERATIONS']},停止调用工具",
            }
        )

    sources = [{"text": d["text"], "score": d["score"]} for d in local_docs]
    return {"trace": trace_events, "sources": sources, "answer": final_content}
