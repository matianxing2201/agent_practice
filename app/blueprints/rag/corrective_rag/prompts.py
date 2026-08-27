"""Corrective-RAG:两个节点的提示词。

核心思路(纠错):检索结果必须经过「相关性评审」——
相关才留下,不相关就放弃,转联网搜索补充,避免拿无关资料硬编答案。
"""

from langchain_core.prompts import ChatPromptTemplate

grade_milvus_docs_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """你是中医病例检索评审专家。
判断检索病例文本是否与用户问诊内容相关。
只输出英文单词：relevant或irrelevant；
禁止输出额外文字。""",
        ),
        (
            "human",
            "----患者描述----\n{patient_desc}\n----病例片段----\n{docs_chunk}",
        ),
    ]
)

generate_answer_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """你是一个AI中医医师，
你需要根据患者描述、中医病例记录、联网搜索信息结果，
为患者作出中医诊断，并给出中医治疗方案。""",
        ),
        (
            "human",
            "----患者描述----\n{patient_desc}\n----中医病例记录----\n{relevant_docs}\n----联网搜索信息结果----\n{web_context}",
        ),
    ]
)