"""Elasticsearch 案例:HTTP 路由(注册到 rag 主题 blueprint)。

URL 前缀 /rag/graph/es:

    GET    /rag/graph/es/status                              连通性 + 版本
    POST   /rag/graph/es/analyze                             IK 分词对比
    POST   /rag/graph/es/indexes                             建索引
    DELETE /rag/graph/es/indexes/<index_name>                删索引
    POST   /rag/graph/es/indexes/<index_name>/docs           写文档:对象单条、数组 bulk
    GET    /rag/graph/es/indexes/<index_name>/docs/<doc_id>  按 id 取单条
    PUT    /rag/graph/es/indexes/<index_name>/docs/<doc_id>  局部更新
    DELETE /rag/graph/es/indexes/<index_name>/docs/<doc_id>  删文档
    POST   /rag/graph/es/indexes/<index_name>/search         检索

search 的 body(字段都可选):
    {
      "keyword": "手机",                     中文关键词 -> match(title/desc) + 高亮
      "query":   {"bool": {...}},           直接给完整 ES 查询 DSL,优先于 keyword
      "sort":    [{"price": "desc"}],       排序
      "from":    0,                         分页起点(不能和 search_after 同时用)
      "size":    5,                         返回条数,不传用配置的 ES_TOP_K
      "search_after": [7999, "1001"],       深分页游标 = 上一页最后一条的 sort
      "highlight": true                     不传时,有关键词就默认开
    }
"""

from elasticsearch import ApiError
from flask import jsonify, request

from ... import bp  # 案例嵌在 graph_rag 下一层,比 naive_rag 多一级(.. 是 graph_rag)
from . import services


@bp.errorhandler(ApiError)
def handle_api_error(exc: ApiError):
    """ES 的 4xx(多半是查询 DSL 或 mapping 写错)原样回给调用者,不要变成 500。

    ApiError 只在 ES 调用里抛,挂在共享的 rag bp 上不会影响其他方案。
    """
    status = exc.status_code if 400 <= exc.status_code < 500 else 502
    return jsonify({"error": str(exc)}), status


@bp.route("/graph/es/status", methods=["GET"])
def es_status():
    """连通性 + 集群信息 + 默认索引状态。连不上返回 503,不会抛异常。"""
    result = services.status()
    return jsonify(result), (200 if result["connected"] else 503)


@bp.route("/graph/es/analyze", methods=["POST"])
def es_analyze():
    """IK 分词对比:POST body {"text": "华为Mate80手机", "analyzers": [...]}

    analyzers 不传时对比 ik_max_word / ik_smart / standard 三个。
    """
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "body 必须是对象"}), 400

    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text 不能为空"}), 400

    analyzers = data.get("analyzers")
    if analyzers is None:
        return jsonify(services.analyze_text(text))
    if not isinstance(analyzers, list) or not analyzers:
        return jsonify({"error": "analyzers 要是非空数组"}), 400
    return jsonify(services.analyze_text(text, tuple(analyzers)))


@bp.route("/graph/es/indexes", methods=["POST"])
def es_create_index():
    """建索引。body 可以省略,默认建 goods_v1 并带上 IK mapping。

    index(索引)的字段是由Mapping来定义的，定义字段类型（数据类型，ES类型）
    中文字段必须指定ik分词器，如果不指定，中文的搜索将完全失效

    ik_max_word: 分最多的分词，适合index存入数据
    ik_smart: 智能分词，适合搜索查询

    1. ES查询类型：
        1. text：模糊搜索使用的类型
        2. keyword：筛选、分组、精准匹配
    2. 索引的mapping创建好后，不能更改，字段结构变化，必须重新创建索引，数据迁移（reindex）
    3. 必须安装ik分词器，否则中文搜索失效（效果差）
    """
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "body 必须是对象"}), 400

    result = services.ensure_index(data.get("index"), data.get("mapping"))
    return jsonify(result), (201 if result["created"] else 200)


@bp.route("/graph/es/indexes/<index_name>", methods=["DELETE"])
def es_drop_index(index_name: str):
    """删索引,连带里面的文档一起删掉。"""
    if not services.drop_index(index_name):
        return jsonify({"error": f"索引 {index_name} 不存在"}), 404
    return "", 204


@bp.route("/graph/es/indexes/<index_name>/docs", methods=["POST"])
def es_insert_docs(index_name: str):
    """写文档:body 是对象 -> 单条;是数组 -> bulk 批量。

    每条的 _id 取 goods_id 字段,方便后面按 id 取 / 改 / 删。
    """
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        docs = [payload]
    elif isinstance(payload, list):
        docs = payload
    else:
        return jsonify({"error": "body 要传一个文档对象,或文档对象数组"}), 400

    if not docs or not all(isinstance(doc, dict) and doc for doc in docs):
        return jsonify({"error": "文档不能为空,且每条都必须是对象"}), 400

    return jsonify(services.insert_docs(docs, index_name)), 201


@bp.route("/graph/es/indexes/<index_name>/docs/<doc_id>", methods=["GET"])
def es_get_doc(index_name: str, doc_id: str):
    """按 _id 取单条"""
    doc = services.get_doc(doc_id, index_name)
    if doc is None:
        return jsonify({"error": f"文档 {doc_id} 不存在"}), 404
    return jsonify({"_id": doc_id, "_source": doc})


@bp.route("/graph/es/indexes/<index_name>/docs/<doc_id>", methods=["PUT"])
def es_update_doc(index_name: str, doc_id: str):
    """局部更新:body 只放要改的字段,如 {"price": 7599}。"""
    partial = request.get_json(silent=True)
    if not isinstance(partial, dict) or not partial:
        return jsonify({"error": "body 要传一个非空对象,只放要改的字段"}), 400

    if not services.update_doc(doc_id, partial, index_name):
        return jsonify({"error": f"文档 {doc_id} 不存在"}), 404
    return jsonify({"_id": doc_id, "updated": list(partial)})


@bp.route("/graph/es/indexes/<index_name>/docs/<doc_id>", methods=["DELETE"])
def es_delete_doc(index_name: str, doc_id: str):
    """删文档。"""
    if not services.delete_doc(doc_id, index_name):
        return jsonify({"error": f"文档 {doc_id} 不存在"}), 404
    return "", 204


@bp.route("/graph/es/indexes/<index_name>/search", methods=["POST"])
def es_search(index_name: str):
    """检索:keyword 和 query 至少给一个,都不给就是 match_all。

    body 里 keyword / query / sort / from / size / search_after / highlight

    （1）简单关键词检索(text 模糊匹配,自动 hit title + desc 两列并高亮):
        { "keyword": "手机" }
        等价于 ES: {"bool": {"should": [{"match": {"title": "手机"}},
                                        {"match": {"desc": "手机"}}]}} + highlight

    （2）bool 复合查询(must/should/filter,优先级高于 keyword,给了就整段透传):
        {
          "query": {
            "bool": {
              "should": [ {"match": {"title": "手机"}}, {"match": {"desc": "手机"}} ],
              "filter": [
                {"term":  {"category": "mobile_phone"}},   # term 用 keyword 字段,精确匹配
                {"range": {"price": {"gte": 7999}}}       # 范围过滤:g e/le/gt/lt
              ]
            }
          }
        }
        must=必须满足(算分)  should=满足其一(算分)  filter=过滤(不算分)

    （3）排序 + 分页(demo_9:match_all + sort + from/size):
        {
          "query": {"match_all": {}},
          "sort":  [{"price": {"order": "desc"}}],   # desc 降序 / asc 升序
          "from":  0,
          "size":  10
        }
        注意:from 不能和 search_after 同时用,只选一种翻页方式。

    （4）search_after 深分页(demo_10:返回带 sort 游标,逐页往下翻):
        {
          "query": {"bool": {"should": [...], "filter": [...]}},
          "sort":  [{"price": "desc"}, {"goods_id": "asc"}],  # 游标排序必须唯一稳定
          "size":  5,
          "search_after": [7999, "1001"]   # = 上一页最后一条返回的 "sort" 字段原样贴回来
        }
        ES 默认最多翻到 10000 条(1w 深分页保护),深翻页要用 search_after 而非 from。
    """
    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        return jsonify({"error": "body 必须是对象"}), 400

    result = services.search_text(
        index_name=index_name,
        keyword=(body.get("keyword") or "").strip() or None,
        query=body.get("query"),
        sort=body.get("sort"),
        from_=body.get("from") or 0,
        size=body.get("size"),
        search_after=body.get("search_after"),
        highlight=body.get("highlight"),
    )
    return jsonify(result)
