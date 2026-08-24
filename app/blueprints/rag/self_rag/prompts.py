"""Self-RAG:四个自省节点的提示词。

参考 5_self_rag,每个节点让 LLM 输出一个固定标记词,
用标记词驱动工作流的路由分支:
    judge_retrieve   RETRIEVE / DIRECT    (要不要检索)
    filter_docs      YES / NO             (这块病历跟患者相关吗,逐块判断)
    check_sufficiency ENOUGH / LACK       (有效资料够不够,不够就重检索)
    generate         自由文本             (最终诊断)
"""

from langchain_core.prompts import ChatPromptTemplate

judge_retrieve_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """任务：判断患者输入的描述信息是否需要检索中医病例知识库。
输出规则：仅输出【RETRIEVE】或【DIRECT】
患者描述的身体症状、舌脉情况、病痛情况、病史情况等中西医问诊问题直接输出RETRIEVE；
闲聊、问候、与医学相关话题无关的问题直接输出DIRECT。""",
        ),
        ("human", "----以下是患者的描述信息----\n{patient_msg}"),
    ]
)

filter_docs_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """判断病例文本与患者描述内容是否具备参考价值，仅输出YES / NO。
标准：
病例包含相似证型、病因、病机、方药记录则为YES；
完全无关则为NO。""",
        ),
        (
            "human",
            "----以下是患者的描述信息----\n{patient_msg}\n----备选病例片段集合----\n{doc_chunk}",
        ),
    ]
)

check_sufficiency_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """判断有效病例记录资料能否完整解答患者疑问。
标准输出：ENOUGH / LACK
具备辨证论治、方药参考直接输出ENOUGH；
缺少关键诊疗信息，需要再次检索知识库直接输出LACK。""",
        ),
        (
            "human",
            "----以下是患者的描述信息----\n{patient_msg}\n----有效病例记录列表----\n{valid_medical_record_list}",
        ),
    ]
)

generate_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """依据提供的中医病例作答，严禁编造证型、病因病机、方药。
输出辩证分析、病因病机、治法、方药与其煎服法。""",
        ),
        (
            "human",
            "----以下是患者的描述信息----\n{patient_msg}\n----有效参考病例----\n{medical_record}",
        ),
    ]
)