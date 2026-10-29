from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..client import get_client
from ..config import Conf

DATA_PATH = Path(__file__).parent / "data" / "证型.txt"
CHROMA_PATH = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "tcm_syndrome"
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50
TOP_K = 3


@lru_cache(maxsize=1)
def _get_vector_store() -> Chroma:
    """创建或加载持久化向量库,避免每次请求都重新切分和向量化。"""
    embeddings = OllamaEmbeddings(
        model=Conf.EMBEDDING_MODEL,
        base_url=Conf.HOST,
    )
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_PATH),
    )

    # 本地向量库为空时,首次读取知识文件并写入切分后的文本。
    if not vector_store.get()["ids"]:
        documents = TextLoader(str(DATA_PATH), encoding="utf-8").load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        chunks = splitter.split_documents(documents)
        vector_store.add_documents(chunks)

    return vector_store


def answer_question(query: str) -> dict:
    """检索证型知识库,并根据命中的内容生成回答。"""
    vector_store = _get_vector_store()
    related_docs = vector_store.similarity_search(query, k=TOP_K)
    context = "\n\n".join(document.page_content for document in related_docs)

    prompt = f"""根据患者自述和中医证型知识库中的相关内容,整理可能相关的证型与治法。
请说明回答依据来自以下资料,仅供学习参考,不能替代医生诊断。

中医证型知识库内容:
{context}

患者自述:
{query}
"""
    response = get_client().generate(
        model=Conf.CHAT_MODEL,
        prompt=prompt,
        options={"num_predict": 256},
    )

    return {
        "answer": response.response,
        "sources": [
            {
                "content": document.page_content,
                "metadata": document.metadata,
            }
            for document in related_docs
        ],
    }
