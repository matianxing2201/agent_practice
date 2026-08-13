"""Service 层:业务逻辑。

职责:业务逻辑——Controller 的请求在这里处理,数据访问暂时也放这层。

设计说明:目前数据访问逻辑还很简单(只有一个占位函数),不值得单独拆
数据访问层;等出现"多处重复的数据代码"或"需要切换数据源"时,再拆。
"""


def get_documents() -> list[str]:
    """读取知识库文档列表。

    占位实现:后续学习时替换为真实数据源(向量数据库、文件系统等)。
    """
    return []


def get_rag_overview() -> dict:
    """返回 RAG 主题概览信息(练习示例:controller -> service 调用链)。"""
    return {
        "topic": "rag",
        "description": "Retrieval-Augmented Generation:检索增强生成",
        "documents": get_documents(),
    }
