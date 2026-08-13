from flask import Blueprint

# url_prefix:本主题所有路由都挂在 /rag 下
bp = Blueprint("rag", __name__, url_prefix="/rag")

# 必须在 bp 定义之后导入,让 controllers 里的 @bp.route 注册到本蓝图
from . import controllers
