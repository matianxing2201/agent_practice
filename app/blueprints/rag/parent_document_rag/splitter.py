"""父子两级切分:RecursiveCharacterTextSplitter。

为什么父子分块(教学核心):
    单层分块有两难——
      切大块:一个块里混多个主题,向量被平均化,检索不准;
      切小块:语义被切碎,召回片段残缺(LLM 拿到半句话)。
    解法是双层表示:父块(大)保全文语义,子块(小)保检索精度。

    本文件只负责「切」:把整篇文档切成 (父块, [子块]) 对。
    RecursiveCharacterTextSplitter 按 段落→句子→标点 递归切分,
    separators 里的中文标点(，。、)专为中文文本设计。
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter

# 参考 4_parent_document_rag:中文长文档(合同/标书/政策)场景
_SEPARATORS = ["\n\n", "\n", "，", "。", "、", " ", ""]


def split_parent_child(
    doc_content: str,
    parent_size: int,
    parent_overlap: int,
    child_size: int,
    child_overlap: int,
) -> list[tuple[str, list[str]]]:
    """整篇文档 -> [(父块文本, [子块文本, ...]), ...]。"""
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=parent_size,
        chunk_overlap=parent_overlap,
        separators=_SEPARATORS,
        keep_separator=True,
    )
    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=child_size,
        chunk_overlap=child_overlap,
        separators=_SEPARATORS,
        keep_separator=True,
    )
    return [
        (p_chunk, child_splitter.split_text(p_chunk))
        for p_chunk in parent_splitter.split_text(doc_content)
    ]
