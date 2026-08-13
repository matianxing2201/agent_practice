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
├── app/
│   ├── __init__.py          # 应用工厂 create_app():加载配置 + 注册蓝图
│   └── blueprints/
│       ├── __init__.py      # 蓝图注册器:新增主题在此加一行注册
│       └── rag/             # 学习主题:RAG(每个主题一个目录)
│           ├── __init__.py  # Blueprint 定义(url_prefix=/rag)
│           ├── controllers.py  # Controller 层:HTTP 请求/响应
│           └── services.py     # Service 层:业务逻辑(含数据访问)
```

## 新增学习主题的步骤(互相解耦)

1. 复制 `app/blueprints/rag/` 为 `app/blueprints/<topic>/`,改目录内 `__init__.py` 的 Blueprint 名和 `url_prefix`
2. 在 `app/blueprints/__init__.py` 的 `register_blueprints()` 里加一行 import + register
3. 完事——现有代码零改动

各层职责:

| 层 | 文件 | 职责 |
|---|---|---|
| Controller | `controllers.py` | 只管请求/响应,不写业务 |
| Service | `services.py` | 业务逻辑,含数据访问 |
| Config | `config.py` | 环境配置 |

> 数据访问目前并入 Service 层:逻辑简单时不需要单独拆层;等出现多处重复的数据代码或需要切换数据源时,再从 Service 中拆出独立的数据访问模块。

## 命名规范(PEP 8)

- 包/模块:全小写 snake_case(`blueprints/rag/`)
- 类:CapWords(`DevelopmentConfig`)
- 函数/变量:snake_case(`get_rag_overview`)
- 常量:全大写(`OPENAI_API_KEY`)
