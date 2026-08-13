"""应用工厂:负责组装整个应用。

create_app() 负责组装整个应用:
1. 创建 Flask 实例,加载配置
2. 注册所有主题蓝图

启动方式:
    flask run                # 通过 wsgi.py(flask 命令零参数自动检测)
    或 python wsgi.py
"""

from flask import Flask

from config import config


def create_app(config_name: str | None = None) -> Flask:
    """创建并配置 Flask 应用实例。

    config_name: "development" / "production" / "testing",缺省用 default。
    """
    app = Flask(__name__)

    # 加载配置类(config_name 为空时用 default)
    app.config.from_object(config.get(config_name or "default", config["default"]))

    # 注册所有主题蓝图(新增主题:去 app/blueprints/ 加目录,注册器里加一行)
    from .blueprints import register_blueprints

    register_blueprints(app)

    return app
