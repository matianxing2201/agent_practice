"""WSGI 入口文件:导出 WSGI 应用对象。

为什么叫 wsgi.py:
- flask run 会自动检测 app.py 和 wsgi.py,零参数即可启动
- 生产部署时 gunicorn 直接用 gunicorn wsgi:app,无需改动

启动:
    flask run
    或 python wsgi.py
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
