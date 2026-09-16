"""Elasticsearch 案例:业务编排层。

controllers 调这里,把「索引建好没 / 写了几条 / 命中什么」组织成对学习
友好的返回。真正的 ES 调用在 es_store 层,查询 DSL 的组装在这一层。

方法对应内容:
    status         连通性 + 集群信息
    analyze_text   分词对比:ik_max_word / ik_smart / standard
    ensure_index   建索引(带 IK mapping)
    drop_index     删索引
    insert_docs    单条 / bulk
    get_doc        按 id 取单条
    update_doc     局部更新
    delete_doc     删文档
    search_text    match + 高亮 /  bool 复合查询
                  / 分页 /  search_after 深分页
"""

from flask import current_app

from .es_store import ID_FIELD, EsStore

# 分词演示用的分析器:IK 两个 + ES 自带的 standard 做对照
ANALYZERS = ("ik_max_word", "ik_smart", "standard")


def _store(index_name: str | None = None) -> EsStore:
    return EsStore(index_name)


def status() -> dict:
    """连通性 + 集群信息 + 默认索引状态。"""
    store = _store()
    if not store.ping():
        return {
            "connected": False,
            "error": (
                f"连不上 {current_app.config['ES_HOST']}:{current_app.config['ES_PORT']},"
                "先确认 docker 里的 es01 起来了"
            ),
        }
    info = store.info()
    return {
        "connected": True,
        "cluster_name": info["cluster_name"],
        "version": info["version"]["number"],
        "index": store.index_name,
        "index_exists": store.index_exists(),
    }


def analyze_text(text: str, analyzers: tuple[str, ...] = ANALYZERS) -> dict:
    """同一段文本用多个分析器各切一遍,对比结果。

    这是理解「中文为什么必须装 IK」最直接的一步:standard 把中文切成
    单字,ik_max_word 切得最细(还会重叠),ik_smart 只切一遍。
    """
    store = _store()
    return {"text": text, "tokens": {name: store.analyze(text, name) for name in analyzers}}


def ensure_index(index_name: str | None = None, mapping: dict | None = None) -> dict:
    """建索引(幂等),返回这次是否真的建了 + 最终的 mapping。"""
    store = _store(index_name)
    created = store.ensure_index(mapping)
    return {"index": store.index_name, "created": created, "mapping": store.index_mapping()}


def drop_index(index_name: str | None = None) -> bool:
    """删索引。索引不存在返回 False。"""
    return _store(index_name).delete_index()


def insert_docs(docs: list[dict], index_name: str | None = None) -> dict:
    """写文档:一条走单条接口,多条走 bulk。

    写之前先 ensure_index:ES 碰到不存在的索引会自动建一个,但那个索引
    是动态 mapping、没有 IK,中文检索直接就废了。
    """
    store = _store(index_name)
    store.ensure_index()

    if len(docs) == 1:
        doc = docs[0]
        doc_id = doc.get(ID_FIELD)
        resp = store.index_doc(doc, str(doc_id) if doc_id is not None else None)
        store.refresh()
        return {"index": store.index_name, "mode": "single", "count": 1, "ids": [resp["_id"]]}

    success, errors = store.bulk_index(docs)
    store.refresh()
    return {
        "index": store.index_name,
        "mode": "bulk",
        "count": success,
        "failed": len(errors),
        "errors": errors[:3],  # 失败明细只回前 3 条,避免刷屏
    }


def get_doc(doc_id: str, index_name: str | None = None) -> dict | None:
    """按 _id 取单条"""
    return _store(index_name).get_doc(doc_id)


def update_doc(doc_id: str, partial: dict, index_name: str | None = None) -> bool:
    """局部更新:只传要改的字段,没传的保持原样。文档不存在返回 False。"""
    store = _store(index_name)
    if not store.update_doc(doc_id, partial):
        return False
    store.refresh()
    return True


def delete_doc(doc_id: str, index_name: str | None = None) -> bool:
    """按 _id 删文档。文档不存在返回 False。"""
    store = _store(index_name)
    if not store.delete_doc(doc_id):
        return False
    store.refresh()
    return True


def search_text(
    index_name: str | None = None,
    keyword: str | None = None,
    query: dict | None = None,
    sort: list | None = None,
    from_: int = 0,
    size: int | None = None,
    search_after: list | None = None,
    highlight: bool | None = None,
) -> dict:
    """检索

    keyword       中文关键词,自动拼成 bool.should(match title / desc) + 高亮
    query         直接给完整 ES query DSL,优先于 keyword
    from_ / size  分页(size 不传时用配置里的 ES_TOP_K
    search_after  深分页游标:把上一页最后一条的 sort 值原样塞回来
    highlight     不传时,有关键词就默认开
    """
    store = _store(index_name)
    if size is None:
        size = current_app.config["RAG_SCHEMES"]["graph_rag"]["ES_TOP_K"]

    body: dict = {"size": size}

    if query is not None:
        body["query"] = query
    elif keyword:
        #  desc 任一边命中都算,should 的命中条数参与打分
        body["query"] = {
            "bool": {
                "should": [
                    {"match": {"title": keyword}},
                    {"match": {"desc": keyword}},
                ]
            }
        }
    else:
        body["query"] = {"match_all": {}}

    # search_after 和 from 不能一起用:要游标翻页就别给 from
    if search_after:
        body["search_after"] = search_after
    elif from_:
        body["from"] = from_

    if sort:
        body["sort"] = sort

    if highlight is None:
        highlight = bool(keyword)
    if highlight:
        body["highlight"] = {"fields": {"title": {}, "desc": {}}}

    resp = store.search(body)
    hits = [
        {
            "_id": hit["_id"],
            "_score": hit.get("_score"),
            "_source": hit["_source"],
            "highlight": hit.get("highlight"),
            "sort": hit.get("sort"),  # 下一页把这条原样塞进 search_after 就是游标
        }
        for hit in resp["hits"]["hits"]
    ]
    return {
        "index": store.index_name,
        "total": resp["hits"]["total"]["value"],
        "took": resp["took"],
        "hits": hits,
    }
