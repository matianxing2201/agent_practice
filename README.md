# 🤖 Agent Practice

AI Agent 学习实践项目。基于 Flask 应用工厂 + 蓝图分层架构，按学习系列组织内容，每个系列独立目录，互不干扰。

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)

---

## 📋 项目简介

本项目是一个 **AI Agent 学习实践平台**，采用模块化架构设计，每个学习系列作为独立蓝图，内部按 Controller / Service 两层分层。

### 核心特性

- 🏗️ **应用工厂模式**：Flask 应用工厂 + 蓝图注册，支持多系列扩展
- 🧩 **模块化设计**：每个学习系列独立目录，互不干扰
- 🧪 **测试覆盖**：HTTP seam 测试，mock 外部依赖

---

## 🗂️ 学习系列

| 系列 | 状态 | 说明 |
|------|------|------|
| [**RAG 系列**](#rag-系列) | ✅ 进行中 | 检索增强生成：索引、检索、生成、流式输出 |
| **Agent 系列** | 🚧 规划中 | 智能体：工具调用、规划、记忆 |
| **Fine-tuning 系列** | 🚧 规划中 | 模型微调：LoRA、DPO、数据准备 |
| **Deployment 系列** | 🚧 规划中 | 部署上线：Docker、CI/CD、监控 |

---

## 📚 RAG 系列

RAG（Retrieval-Augmented Generation，检索增强生成）系列，从零实现完整的 RAG 全链路。

### 系列内容

| 阶段 | 模块 | 核心概念 | 实现文件 |
|------|------|----------|----------|
| **Indexing（索引）** | knowledge_base | 文档切分、向量化、Milvus 写入 | `knowledge_base/` |
| **Retrieval（检索）** | naive_rag | 问题向量化、相似度检索、top_k | `retrieval.py` |
| **Generation（生成）** | naive_rag | prompt 组装、LLM 调用、流式输出 | `generation.py` |

### 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      Flask Application                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   knowledge_base │  │    naive_rag    │  │   (future)   │ │
│  │   (数据管理者)   │  │   (数据使用者)  │  │   (其他方案)  │ │
│  ├─────────────────┤  ├─────────────────┤  ├──────────────┤ │
│  │ controllers.py  │  │ controllers.py  │  │    ...       │ │
│  │ services.py     │  │ services.py     │  │              │ │
│  │ milvus_store.py │  │ retrieval.py    │  │              │ │
│  │                 │  │ generation.py   │  │              │ │
│  └────────┬────────┘  └────────┬────────┘  └──────────────┘ │
│           │                    │                             │
│           └────────┬───────────┘                             │
│                    ▼                                         │
│           ┌─────────────────┐                               │
│           │   config.py     │                               │
│           │ (统一配置管理)  │                               │
│           └─────────────────┘                               │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │      Milvus          │
              │  (向量数据库)         │
              └───────────────────────┘
```

### API 接口

#### 知识库管理（knowledge_base）

| 接口 | 方法 | 功能 |
|------|------|------|
| `/rag/knowledge/upload` | POST | 上传 `.txt` 文件批量导入 |
| `/rag/knowledge` | POST | 手动输入单条记录 |
| `/rag/knowledge` | GET | 分页列表 |
| `/rag/knowledge/<id>` | GET | 单条详情 |
| `/rag/knowledge/<id>` | PUT | 更新记录（自动重新向量化） |
| `/rag/knowledge/<id>` | DELETE | 删除记录 |

#### Naive RAG 方案

| 接口 | 方法 | 功能 |
|------|------|------|
| `/rag/naive/query` | POST | 提问，触发检索 + 流式生成 |

**SSE 事件格式：**

```
data: {"type": "sources", "sources": [{"text": "...", "score": 0.9}]}

data: {"type": "delta", "content": "你"}

data: {"type": "delta", "content": "好"}

data: {"type": "done"}
```

---

## 🚀 快速开始

### 环境要求

- Python 3.13+
- Docker（运行 Milvus）
- 智谱 API Key（Embedding 服务）

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
│   └── test_naive_rag.py
└── app/
    ├── __init__.py          # 应用工厂 create_app()
    └── blueprints/
        ├── __init__.py      # 蓝图注册器
        └── rag/             # RAG 学习系列
            ├── __init__.py  # Blueprint 定义 (url_prefix=/rag)
            ├── knowledge_base/  # 知识库管理模块
            │   ├── controllers.py
            │   ├── services.py
            │   └── milvus_store.py
            └── naive_rag/   # Naive RAG 方案
                ├── controllers.py
                ├── services.py
                ├── retrieval.py
                └── generation.py
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
| `CHUNK_SIZE` | 文本切分大小 | `500` |
| `CHUNK_OVERLAP` | 切分重叠 | `50` |

---

## 📚 扩展指南

### 新增学习系列

1. 在 `app/blueprints/` 下创建新系列目录（如 `agent/`）
2. 在 `app/blueprints/__init__.py` 中注册蓝图
3. 按 Controller / Service 分层实现
4. 在 `config.py` 中添加相关配置

### 新增 RAG 方案

1. 复制 `naive_rag/` 目录为新方案目录
2. 修改 `__init__.py` 的 Blueprint 名和 `url_prefix`
3. 在 `config.py` 的 `RAG_SCHEMES` 中添加新 collection 配置
4. 在 `rag/__init__.py` 中注册新蓝图
5. 实现 retrieval.py 和 generation.py

---

## 📄 License

MIT

---

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [Milvus](https://milvus.io/) - 向量数据库
- [智谱 AI](https://open.bigmodel.cn/) - Embedding 服务
