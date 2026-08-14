"""知识库管理:HTTP 路由(注册到 rag 主题 blueprint)。

URL 前缀 /rag/knowledge,提供完整 CRUD:
    POST   /rag/knowledge            手动输入单条
    POST   /rag/knowledge/upload     .txt 文件批量导入
    GET    /rag/knowledge            分页列表
    GET    /rag/knowledge/<id>       单条详情
    PUT    /rag/knowledge/<id>       改 text(自动重新向量化)
    DELETE /rag/knowledge/<id>       按 id 删除
"""

from flask import jsonify, request

from .. import bp
from . import services


@bp.route("/knowledge/upload", methods=["POST"])
def upload_file():
    """.txt 文件批量导入:POST /rag/knowledge/upload(multipart 的 file 字段)"""
    file = request.files.get("file")
    if file is None or not file.filename:
        return jsonify({"error": "缺少文件"}), 400
    if not file.filename.lower().endswith(".txt"):
        return jsonify({"error": "仅支持 .txt 文件"}), 400
    content = file.read().decode("utf-8")
    count = services.import_file(content)
    return jsonify({"count": count}), 201


@bp.route("/knowledge", methods=["POST"])
def create_record():
    """手动输入单条:POST /rag/knowledge,body 为 JSON {"text": "..."}"""
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text 不能为空"}), 400
    record_id = services.create_record(text)
    return jsonify({"id": record_id}), 201


@bp.route("/knowledge/<int:record_id>", methods=["DELETE"])
def delete_record(record_id: int):
    """删除单条:DELETE /rag/knowledge/<id>"""
    if not services.delete_record(record_id):
        return jsonify({"error": "记录不存在"}), 404
    return "", 204


@bp.route("/knowledge/<int:record_id>", methods=["PUT"])
def update_record(record_id: int):
    """修改单条:PUT /rag/knowledge/<id>,body 为 JSON {"text": "..."}"""
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text 不能为空"}), 400
    if not services.update_record(record_id, text):
        return jsonify({"error": "记录不存在"}), 404
    return jsonify({"id": record_id})


@bp.route("/knowledge/<int:record_id>", methods=["GET"])
def get_record(record_id: int):
    """单条详情:GET /rag/knowledge/<id>"""
    record = services.get_record(record_id)
    if record is None:
        return jsonify({"error": "记录不存在"}), 404
    return jsonify(record)


@bp.route("/knowledge", methods=["GET"])
def list_records():
    """分页列表:GET /rag/knowledge?page=1&size=20"""
    page = request.args.get("page", 1, type=int)
    size = request.args.get("size", 20, type=int)
    return jsonify(services.list_records(page, size))
