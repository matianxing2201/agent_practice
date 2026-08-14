"""阶段 3:Generation 生成——LLM 基于检索结果回答。

目标:让模型「只依据提供的资料」回答,这是 RAG 减少幻觉的关键。

关键步骤:
    1. 组装 prompt
       系统提示(明确"只依据提供的资料回答,不要编造")
       + 检索到的片段(拼接为上下文)
       + 用户问题。
    2. 调用 LLM
       OpenCode Zen 的 deepseek-v4-flash(OpenAI 兼容接口),
       模型与凭据见项目根 config.py:CHAT_MODEL / CHAT_BASE_URL / CHAT_API_KEY。
    3. 输出
       返回回答;可附带引用的资料来源(片段来源),便于校验。

涉及概念:prompt 设计、上下文窗口限制、引用溯源。

前置条件:retrieval 已返回 top_k 片段。
"""
