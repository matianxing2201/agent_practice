"""Ollama + ChromaDB 的 RAG。

1. TextLoader 读取 data/证型.txt
2. RecursiveCharacterTextSplitter 切分(chunk_size=300, overlap=50)
3. OllamaEmbeddings(模型取 config.OLLAMA_EMBEDDING_MODEL)向量化
4. ChromaDB 持久化到 chroma_db/,collection = tcm_syndrome
5. 检索 top_k 片段 -> 拼 prompt -> ollama.generate

"""

from . import controllers  # noqa: E402,F401
