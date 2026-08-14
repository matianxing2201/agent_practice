# Agent Practice

AI Agent 练习项目。采用 Flask 应用工厂 + 按主题分目录的蓝图架构,每个学习主题内部按 controller / service 两层分层。

## 启动

```bash
source .venv/bin/activate
cp .env.example .env    # 首次:填入 SECRET_KEY / OPENAI_API_KEY

flask run               # flask 命令自动检测 wsgi.py,零参数启动
```

启动后访问 <http://127.0.0.1:5000/rag/> 验证。

## 目录结构

```
agent_practice/
├── wsgi.py                  # 入口:app = create_app()(flask/gunicorn 通用)
├── config.py                # 配置层:Config 类继承 + .env 读取
├── .flaskenv                # Flask CLI 配置(FLASK_APP/FLASK_DEBUG,提交 git)
├── .env                     # 密钥(不入 git)
├── knowledge_base/          # RAG 知识库文档(病历等私有数据,不入 git)
├── docs/specs/              # 需求规格文档
├── tests/                   # pytest 测试(HTTP seam)
├── app/
│   ├── __init__.py          # 应用工厂 create_app():加载配置 + 注册蓝图
│   └── blueprints/
│       ├── __init__.py      # 蓝图注册器:新增主题在此加一行注册
│       └── rag/             # 学习主题:RAG(只做蓝图容器)
│           ├── __init__.py  # Blueprint 定义(url_prefix=/rag)
│           ├── knowledge_base/ # 知识库管理模块(数据资产管理层)
│           │   ├── __init__.py    # 模块说明
│           │   ├── controllers.py # Controller:HTTP 路由(/rag/knowledge/*)
│           │   ├── services.py    # Service:分割/向量化/编排
│           │   └── milvus_store.py# Milvus 数据访问(增删改查)
│           └── naive_rag/      # 方案:RAG 变种每个一个子目录(方案内分层)
│               ├── __init__.py    # 方案总览:三段式流程说明
│               ├── controllers.py # Controller 层:HTTP 路由(/rag/naive/*)
│               ├── services.py    # Service 层:业务编排
│               ├── indexing.py    # 阶段1 索引:文档->切分->向量化->Milvus
│               ├── retrieval.py   # 阶段2 检索:问题->Milvus 相似度搜索
│               └── generation.py  # 阶段3 生成:prompt 组装->LLM 回答
```

> 配置统一在根目录 `config.py` 管理(模型/凭据/Milvus/collection/索引检索参数)。
> 新增 RAG 方案时:复制 `naive_rag/` 目录(不含 config,因为没有),并在
> `config.py` 的 `RAG_SCHEMES` 里加一个条目指定新 collection 名。

## 新增学习主题的步骤(互相解耦)

1. 复制 `app/blueprints/rag/` 为 `app/blueprints/<topic>/`,改目录内 `__init__.py` 的 Blueprint 名和 `url_prefix`
2. 在 `app/blueprints/__init__.py` 的 `register_blueprints()` 里加一行 import + register
3. 完事——现有代码零改动

各层职责(在每个 RAG 方案目录内):

| 层 | 文件 | 职责 |
|---|---|---|
| Controller | `controllers.py` | 只管请求/响应,不写业务 |
| Service | `services.py` | 业务编排,含数据访问 |
| 阶段实现 | `indexing/retrieval/generation.py` | Naive RAG 三个阶段的实现 |
| Config | `config.py` | 环境配置 |

> 数据访问并入 Service/阶段实现:逻辑简单时不需要单独拆层;等出现多处重复的数据代码或需要切换数据源时,再从 Service 中拆出独立的数据访问模块。

## 命名规范(PEP 8)

- 包/模块:全小写 snake_case(`blueprints/rag/`)
- 类:CapWords(`DevelopmentConfig`)
- 函数/变量:snake_case(`answer_question`)
- 常量:全大写(`OPENAI_API_KEY`)
