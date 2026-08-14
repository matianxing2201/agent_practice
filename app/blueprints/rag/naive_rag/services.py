"""Service 层:Naive RAG 业务编排。

Controller 调用这里的函数,这里按流程编排三个阶段:

    index_document(...)    导入文档 -> indexing.py 切分/向量化/写 Milvus
    answer_question(...)   提问 -> retrieval.py 检索 -> generation.py 生成

职责:业务逻辑的组织者;不处理 HTTP,不直接写外部依赖细节
(调用细节在各阶段文件中)。
"""


def get_overview() -> dict:
    """返回方案概览(链路测试用:controller -> service)。"""
    return {
        "scheme": "naive_rag",
        "name": "Naive RAG",
        "description": "检索增强生成(基础版):索引 -> 检索 -> 生成",
        "stages": ["indexing", "retrieval", "generation"],
        "status": "ok",
    }
