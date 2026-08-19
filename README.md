# 🤖 Agent Practice

AI Agent 学习实践项目。基于 Flask 应用工厂 + 蓝图分层架构，从零实现 RAG（检索增强生成）全链路，包含 **Naive RAG（朴素检索）**、**Hybrid RAG（混合检索）**、**Agentic RAG（自主决策检索）** 三种方案。

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Milvus](https://img.shields.io/badge/Milvus-2.x-00A1E0?logo=milvus&logoColor=white)](https://milvus.io/)

---

## 📋 项目简介

本项目是一个 **AI Agent 学习实践平台**，采用模块化架构设计，每个学习主题（如 RAG）作为独立蓝图，内部按 Controller / Service 两层分层。

### 核心特性

- 🏗️ **应用工厂模式**：Flask 应用工厂 + 蓝图注册，支持多主题扩展
- 🔍 **RAG 全链路**：索引 → 检索 → 生成，完整实现检索增强生成
- ⚡ **输出方式**：naive / hybrid 用 SSE 流式逐字输出；agentic 由 LLM 自主决策调工具后 JSON 返回
- 🧩 **模块化设计**：每个 RAG 方案独立目录，互不干扰
- 🧪 **测试覆盖**：HTTP seam 测试，mock 外部依赖

### 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| Web 框架 | Flask 3.x | HTTP 服务、蓝图路由 |
| 向量数据库 | Milvus 2.x | 向量存储与相似度检索 |
| Embedding | 智谱 embedding-3 | 文本向量化（2048 维） |
| LLM | DeepSeek v4 Flash | 对话生成（OpenAI 兼容接口） |
| 测试 | pytest | HTTP seam 测试 |

---

## 🗺️ 学习路线

本项目按 RAG（检索增强生成）的三个标准阶段组织学习内容：

| 阶段 | 模块 | 核心概念 |
|------|------|----------|
| **Indexing（索引）** | knowledge_base | 文档切分、向量化、Milvus 写入 |
| **Retrieval（检索）** | naive_rag | 向量 top_k |
| **Retrieval（检索）** | hybrid_rag | 向量召回 + BM25 重排 |
| **Retrieval（检索）** | agentic_rag | LLM 自主决策调工具（本地 + 联网） |
| **Generation（生成）** | naive / hybrid | SSE 流式输出 |
| **Generation（生成）** | agentic_rag | JSON 返回 |

### 知识库管理（knowledge_base）

独立于具体 RAG 方案的数据管理层，提供完整 CRUD：

| 接口 | 方法 | 功能 |
|------|------|------|
| `/rag/knowledge/upload` | POST | 上传 `.txt` 文件批量导入 |
| `/rag/knowledge` | POST | 手动输入单条记录 |
| `/rag/knowledge` | GET | 分页列表 |
| `/rag/knowledge/<id>` | GET | 单条详情 |
| `/rag/knowledge/<id>` | PUT | 更新记录（自动重新向量化） |
| `/rag/knowledge/<id>` | DELETE | 删除记录 |

### Naive RAG 方案

最基础的 RAG 实现，**检索 + 生成**：

| 接口 | 方法 | 功能 |
|------|------|------|
| `/rag/naive/query` | POST | 提问，触发检索 + 流式生成 |

**检索方式**：单路向量检索 —— 问题向量化后按 Milvus 相似度取 top_k。

### Hybrid RAG 方案

在 Naive 基础上改进检索：**向量召回 + BM25 关键词重排**，过滤语义相近但字面不相关的噪声（术语精确场景更优）：

| 接口 | 方法 | 功能 |
|------|------|------|
| `/rag/hybrid/query` | POST | 提问，触发混合检索 + 流式生成 |

**检索方式**：向量召回（宽，`CANDIDATE_K` 条候选）→ BM25 关键词重排（窄，取 `TOP_K` 条）。

### Agentic RAG 方案

把**检索封装成工具**，交给 LLM 自主决策——要不要查、查哪里（本地知识库 / Tavily 联网）、查几次（子查询），LangChain Agent 跑完整 ReAct 循环：

| 接口 | 方法 | 功能 |
|------|------|------|
| `/rag/agentic/query` | POST | 提问，LLM 自主决策调用工具 |

**返回格式**：JSON `{trace, sources, answer}`——`trace` 展示「决策 → 观察」推理链（教学可见性），`sources` 为本地引用片段，`answer` 为最终答案。

**SSE 事件格式（naive / hybrid 共用）：**

```
data: {"type": "sources", "sources": [{"text": "...", "score": 0.9}]}

data: {"type": "delta", "content": "你"}

data: {"type": "delta", "content": "好"}

data: {"type": "done"}
```

---

## 🏛️ 架构设计

```
┌─────────────────────────────────────────────────────┐
│                  Flask Application                  │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐  │
│  │ knowledge_base│ │  naive_rag   │ │ hybrid_rag  │  │
│  │  (数据管理者)  │ │ (数据使用者)  │ │(数据使用者) │  │
│  └──────────────┘ └──────────────┘ └─────────────┘  │
│  ┌──────────────┐ ┌──────────────────────────────┐  │
│  │  agentic_rag │ │         config.py            │  │
│  │ (数据使用者)  │ │      (统一配置管理)           │  │
│  └──────────────┘ └──────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
              ┌───────────────────────┐
              │      Milvus          │
              │  (向量数据库)         │
              └───────────────────────┘
```

> 各方案只依赖 knowledge_base（数据管理统一入口），方案之间互不 import（解耦）；后续新方案沿用此模式。

### 分层职责

| 层 | 职责 | 说明 |
|----|------|------|
| **Controller** | 请求/响应处理 | 解析参数、调用 Service、返回 JSON |
| **Service** | 业务编排 | 组织检索、生成等业务流程 |
| **Store** | 数据访问 | Milvus CRUD（仅 knowledge_base） |

### 数据流

```
用户提问
    │
    ▼
┌─────────────┐    ┌─────────────┐    ┌──────────────┐
│  Retrieval  │───▶│  Generation │───▶│  输出         │
│  (检索)     │    │  (生成)     │    │  SSE / JSON  │
└─────────────┘    └─────────────┘    └──────────────┘
       │                  │
       ▼                  ▼
┌─────────────┐    ┌─────────────┐
│   Milvus    │    │   LLM API   │
│  (向量库)   │    │  (DeepSeek) │
└─────────────┘    └─────────────┘
```

---

## 🚀 快速开始

### 环境要求

- Python 3.13+
- Docker（运行 Milvus）
- 智谱 API Key（Embedding 服务）
- Tavily API Key（Agentic 联网搜索，可选）

### 1. 克隆项目

```bash
git clone git@github.com:matianxing2201/agent_practice.git
cd agent_practice
```

### 2. 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的配置：
# - EMBEDDING_API_KEY: 智谱 API Key
# - TOP_K: 检索返回的片段数量（默认 3）
```

### 4. 启动 Milvus

```bash
# 使用 Docker Compose 启动 Milvus
docker-compose up -d
```

### 5. 启动应用

```bash
flask run
```

访问 http://127.0.0.1:5000/ 验证。

---

## 📁 目录结构

```
agent_practice/
├── wsgi.py                  # 入口: app = create_app()
├── config.py                # 配置层: Config 类 + .env 读取
├── .flaskenv                # Flask CLI 配置
├── .env                     # 密钥（不入 git）
├── requirements.txt         # Python 依赖
├── knowledge_base/          # RAG 知识库文档（不入 git）
├── tests/                   # pytest 测试
│   ├── conftest.py          # 测试 fixtures
│   ├── test_knowledge_crud.py
│   ├── test_naive_rag.py
│   ├── test_hybrid_rag.py
│   └── test_agentic_rag.py
└── app/
    ├── __init__.py          # 应用工厂 create_app()
    └── blueprints/
        ├── __init__.py      # 蓝图注册器
        └── rag/             # RAG 学习主题
            ├── __init__.py  # Blueprint 定义 (url_prefix=/rag)
            ├── knowledge_base/  # 知识库管理模块
            │   ├── controllers.py
            │   ├── services.py
            │   └── milvus_store.py
            ├── naive_rag/   # 方案① 单路向量检索
            │   ├── controllers.py
            │   ├── services.py
            │   ├── retrieval.py
            │   └── generation.py
            ├── hybrid_rag/  # 方案② 向量 + BM25 重排
            │   ├── controllers.py
            │   ├── services.py
            │   ├── retrieval.py
            │   └── generation.py
            └── agentic_rag/ # 方案③ LLM 自主决策
                ├── controllers.py
                ├── services.py
                ├── tools.py       # @tool 工具:本地检索 / Tavily 联网
                ├── prompts.py     # 系统提示词
                └── __init__.py
```

---

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_naive_rag.py -v
```

测试使用 mock 替换外部依赖（Embedding API、Milvus），无需真实 API Key 即可运行。

---

## 🔧 配置说明

所有配置统一在 `config.py` 管理，敏感信息从 `.env` 读取：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `EMBEDDING_API_KEY` | 智谱 API Key | - |
| `EMBEDDING_MODEL` | Embedding 模型 | `embedding-3` |
| `EMBEDDING_DIM` | 向量维度 | `2048` |
| `CHAT_API_KEY` | LLM API Key | `opencode-zen` |
| `CHAT_MODEL` | LLM 模型 | `deepseek-v4-flash` |
| `MILVUS_HOST` | Milvus 地址 | `127.0.0.1` |
| `MILVUS_PORT` | Milvus 端口 | `19530` |
| `TOP_K` | 检索返回数量 | `3` |
| `CANDIDATE_K` | 混合检索向量召回候选数 | `5` |
| `MAX_ITERATIONS` | Agentic ReAct 循环迭代上限 | `5` |
| `TAVILY_API_KEY` | Tavily 联网搜索 Key（agentic） | - |
| `CHUNK_SIZE` | 文本切分大小 | `500` |
| `CHUNK_OVERLAP` | 切分重叠 | `50` |

---

## 📚 扩展指南

### 新增 RAG 方案

1. 复制现有方案目录（如 `naive_rag/`）为新方案目录
2. 在 `config.py` 的 `RAG_SCHEMES` 中添加新方案配置（含 `COLLECTION_NAME`）
3. 在 `rag/__init__.py` 中导入新方案注册路由
4. 实现方案代码（naive/hybrid 用 `retrieval.py` + `generation.py`；agentic 用 `tools.py` + `prompts.py` + `create_agent`）
5. 注意：多个方案的 controller 路由函数名不要重复（Flask 端点冲突）

### 新增学习主题

1. 在 `app/blueprints/` 下创建新主题目录
2. 在 `app/blueprints/__init__.py` 中注册蓝图
3. 按 Controller / Service 分层实现

---

## 📄 License

MIT

---

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [Milvus](https://milvus.io/) - 向量数据库
- [智谱 AI](https://open.bigmodel.cn/) - Embedding 服务
- [LangChain](https://www.langchain.com/) - LLM 应用框架
