"""配置层:集中管理应用配置。

用法:应用工厂通过 config_name 选择配置类:
    create_app("development")   # 开发环境
    create_app("production")    # 生产环境
不传则用 default。

密钥等敏感信息从 .env 读取(不入 git),配置类只做读取和分类。

模型服务分两组:
    EMBEDDING_*  向量化服务(智谱 embedding-3)
    CHAT_*       对话生成服务(OpenCode Zen,OpenAI 兼容)

RAG 方案配置统一在此管理(RAG_SCHEMES),各方案目录下不再单独建 config 文件。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 加载项目根目录的 .env(密钥)
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / ".env")


class Config:
    """基础配置:所有环境共用的值。"""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-key")

    # --- Embedding 服务:智谱(ZhipuAI)---
    EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")  # 智谱 key,格式 xxx.xxx
    EMBEDDING_BASE_URL = os.getenv(
        "EMBEDDING_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"
    )
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "embedding-3")

    # --- Chat 服务:OpenCode Zen(OpenAI 兼容)---
    # 端点公开访问,无需真实 key,任意非空值即可
    CHAT_API_KEY = os.getenv("CHAT_API_KEY", "opencode-zen")
    CHAT_BASE_URL = os.getenv("CHAT_BASE_URL", "https://opencode.ai/zen/go/v1")
    CHAT_MODEL = os.getenv("CHAT_MODEL", "deepseek-v4-flash")

    # --- 联网搜索:Tavily(agentic_rag 的 search_online_tool 使用)---
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

    # --- Milvus(全局统一)---
    MILVUS_HOST = "127.0.0.1"
    MILVUS_PORT = "19530"
    METRIC_TYPE = "COSINE"       # 向量相似度度量:IP(内积)/ COSINE / L2
    EMBEDDING_DIM = 2048         # 必须与 embedding 模型输出维度一致(embedding-3)

    # --- RAG 索引/检索默认参数 ---
    CHUNK_SIZE = 500             # 每块文本的最大字符数
    CHUNK_OVERLAP = 50           # 相邻块重叠字符数(保留上下文连续性)
    TOP_K = int(os.getenv("TOP_K", 3))  # 检索返回最相似的片段数量

    # --- RAG 方案配置 ---
    # 新增学习方案:在这里加一个条目即可,无需新建 config 文件
    RAG_SCHEMES = {
        "naive_rag": {
            "COLLECTION_NAME": "tcm_medical_record",  # 中医病历知识库
        },
        "hybrid_rag": {
            "COLLECTION_NAME": "tcm_medical_record",  # 复用同一知识库
            "CANDIDATE_K": 5,  # 向量召回候选数(大于 TOP_K,供 BM25 重排序)
        },
        "agentic_rag": {
            "COLLECTION_NAME": "tcm_medical_record",  # 复用同一知识库
            "TOP_K": 3,  # 本地检索工具返回的片段数(参考代码用 2,这里与全局一致)
            "MAX_ITERATIONS": 5,  # ReAct 循环迭代上限,防止 Agent 无限调用工具
        },
    }

    # --- 知识库目录(索引阶段从这里读文档)---
    KNOWLEDGE_BASE_DIR = os.getenv("KNOWLEDGE_BASE_DIR", str(basedir / "knowledge_base"))


class DevelopmentConfig(Config):
    """开发环境配置。"""

    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置。"""

    DEBUG = False


class TestingConfig(Config):
    """测试环境配置。"""

    TESTING = True
    EMBEDDING_API_KEY = "test-key-not-real"


# 配置注册表:create_app 用字符串索引选择环境
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
