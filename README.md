# 🤖 Agent Practice

Flask 应用工厂 + 蓝图分层的 AI Agent 学习实践项目，从零实现 RAG 全链路，覆盖 **Naive / Hybrid / Agentic / Parent-Document / Self RAG / Corrective-RAG** 六种方案；**Graph RAG**（Elasticsearch + Neo4j）基础设施已搭建，实现进行中。

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Milvus](https://img.shields.io/badge/Milvus-2.x-00A1E0?logo=milvus&logoColor=white)](https://milvus.io/)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.x-005571?logo=elasticsearch&logoColor=white)](https://www.elastic.co/elasticsearch)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.x-4581C3?logo=neo4j&logoColor=white)](https://neo4j.com/)

---

## 🧰 技术栈

| 组件 | 技术 | 用途 |
| ---- | ---- | ---- |
| Web 框架 | Flask 3.x | HTTP 服务、蓝图路由 |
| 向量数据库 | Milvus 2.x | 向量存储与相似度检索 |
| 全文检索 | Elasticsearch 8.x + IK | 关键词 / 中文分词 / Graph RAG 混合检索 |
| 图数据库 | Neo4j 5.x | Graph RAG 实体关系存储与图查询 |
| Embedding | 智谱 embedding-3 | 文本向量化（2048 维） |
| LLM | DeepSeek v4 Flash | 对话生成（OpenAI 兼容接口） |
| 测试 | pytest | HTTP seam 测试，mock 外部依赖 |

---

## 🗺️ 方案概览

| 方案 | 检索方式 / 特点 | 接口 | 输出 |
| ---- | --------------- | ---- | ---- |
| knowledge_base | 知识库管理（数据写入 / CRUD） | `/rag/knowledge`（POST/GET）、`/rag/knowledge/<id>`（GET/PUT/DELETE）、`/rag/knowledge/upload` | JSON |
| naive_rag | 单路向量检索 top_k | `/rag/naive/query` | SSE |
| hybrid_rag | 向量召回 + BM25 重排 | `/rag/hybrid/query` | SSE |
| agentic_rag | LLM 自主决策调工具（本地 + Tavily 联网），ReAct 循环 | `/rag/agentic/query` | JSON `{trace, sources, answer}` |
| parent_document_rag | 父子分块：子块检索、父块返回 | `/rag/parent/upload`、`/rag/parent/query` | SSE |
| self_rag | 自省工作流：判断是否检索、相关性、够用即生成，不足重检索 | `/rag/self/query` | JSON `{answer, sources, retrieve_round}` |
| corrective_rag | 检索后相关性评审，不足转网络补充 | `/rag/corrective/query` | SSE |
| graph_rag（进行中） | ES 关键词 + Milvus 向量 + Neo4j 图检索，多路融合 | 待注册 | - |

> naive / hybrid 的 SSE 格式：先 `sources`（参考来源）→ `delta`（逐字回答）→ `done`。

---

## 🏛️ 架构设计

```
┌─────────────────────────────────────────────────────┐
│                  Flask Application                  │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐  │
│  │ knowledge_base│ │  naive_rag   │ │ hybrid_rag  │  │
│  │ agentic_rag  │ │parent_doc_rag│ │  self_rag   │  │
│  │corrective_rag│ │  graph_rag*  │ │  config.py  │  │
│  └──────────────┘ └──────────────┘ └─────────────┘  │
│  * graph_rag 实现进行中                              │
└─────────────────────────────────────────────────────┘
           ▼                ▼                ▼
       Milvus         Elasticsearch       Neo4j
     (向量数据库)     (+ IK 中文分词)    (图数据库)
```

各方案只依赖 `knowledge_base`（数据管理统一入口），方案间互不 import；graph_rag 额外组合 ES 关键词与 Neo4j 图检索。

**分层**：Controller（请求/响应）→ Service（业务编排）→ Store（数据访问）。

---

## 🚀 快速开始

```bash
git clone git@github.com:matianxing2201/agent_practice.git && cd agent_practice

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # 填入 EMBEDDING_API_KEY 等

docker-compose up -d   # 启动 Milvus

flask run
```

访问 http://127.0.0.1:5000/ 验证。

> Graph RAG 需额外启动 ES + Neo4j（见 `~/Documents/software/elastic-neo4j/`），当前未注册蓝图，不影响基础方案运行。

---

## 📁 目录结构

```
agent_practice/
├── wsgi.py                # 入口: app = create_app()
├── config.py              # 统一配置（含 RAG_SCHEMES）
├── requirements.txt
├── tests/                 # pytest（conftest + 各方案测试）
└── app/
    └── blueprints/rag/
        ├── __init__.py    # Blueprint (url_prefix=/rag)，集中注册各方案
        ├── knowledge_base/       # 数据管理（milvus_store）
        ├── naive_rag/            # ① 单路向量检索
        ├── hybrid_rag/           # ② 向量 + BM25
        ├── agentic_rag/          # ③ LLM 自主决策（tools.py + ReAct）
        ├── parent_document_rag/  # ④ 父子分块（splitter + store）
        ├── self_rag/             # ⑤ 自省工作流（LangGraph 状态机）
        ├── corrective_rag/       # ⑥ 纠错 RAG（LangGraph 状态机）
        └── graph_rag/            # ⑦ Graph RAG（进行中）
            ├── elasticsearch/    #    ES 关键词检索（es_store）
            └── neo4j/            #    Neo4j 图存储（neo4j_store）
```

---

## 🧪 测试

```bash
pytest tests/ -v          # 所有测试；不加 -v 亦可
pytest tests/test_naive_rag.py -v   # 单测
```

测试 mock 外部依赖，无需真实 API Key。

---

## 🔧 配置说明

敏感信息从 `.env` 读取（`config.py`）：

| 配置项 | 说明 | 默认值 |
| ------ | ---- | ------ |
| `EMBEDDING_API_KEY` | 智谱 API Key | - |
| `EMBEDDING_MODEL` / `EMBEDDING_DIM` | 向量化模型 / 维度 | `embedding-3` / `2048` |
| `CHAT_MODEL` | LLM 模型 | `deepseek-v4-flash` |
| `MILVUS_HOST` / `MILVUS_PORT` | Milvus 地址 / 端口 | `127.0.0.1` / `19530` |
| `ES_HOST` / `ES_PORT` | Elasticsearch 地址 / 端口 | `127.0.0.1` / `9200` |
| `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` | Neo4j 连接 | `bolt://127.0.0.1:7687` / `neo4j` / from `.env` |
| `TOP_K` / `CHUNK_SIZE` / `CHUNK_OVERLAP` | 检索与切分参数 | `3` / `500` / `50` |
| `TAVILY_API_KEY` | Tavily 联网搜索 Key（agentic） | - |

各方案的专属配置（`COLLECTION_NAME`、`CANDIDATE_K`、`PARENT_CHUNK_SIZE`、`ES_INDEX` 等）统一在 `config.py` 的 `RAG_SCHEMES` 中管理。

---

## 📚 扩展指南

- **新增 RAG 方案**：复制现有方案目录 → 在 `RAG_SCHEMES` 加配置 → 在 `rag/__init__.py` 注册路由（注意 controller 函数名勿重复）。
- **新增学习主题**：在 `app/blueprints/` 新建目录 → 在 `app/blueprints/__init__.py` 注册蓝图 → 按 Controller / Service 分层实现。

---

## 📄 License · 🙏 致谢

MIT · Flask / Milvus / Elasticsearch / Neo4j / 智谱 AI / LangChain