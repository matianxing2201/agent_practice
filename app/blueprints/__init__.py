"""蓝图注册器:所有主题蓝图在此统一注册。

新增学习主题的步骤:
1. 在 app/blueprints/ 下新建 <topic>/ 目录(复制 rag/ 的结构)
2. 在下方 import 新主题的 bp 并 register_blueprint 一行
现有代码零改动。
"""

from flask import Flask


def register_blueprints(app: Flask) -> None:
    """注册所有主题蓝图。"""

    from .rag import bp as rag_bp

    app.register_blueprint(rag_bp)
