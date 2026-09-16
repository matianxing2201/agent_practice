"""Elasticsearch 数据访问层:elasticsearch-py 8.x 客户端封装。

连接 Elasticsearch 的索引 / 文档 / 查询 / 分词操作。
连接参数读 current_app.config(ES_HOST / ES_PORT,定义于项目根 config.py),
索引默认名读 RAG_SCHEMES["graph_rag"]["ES_INDEX"](默认 goods_v1)。

本层只做「把 ES 的 API 包成方法
逻辑,放在 services 层。

goods_v1 mapping:
    title / desc   text     中文必须指定 IK:写索引用 ik_max_word,查用 ik_smart
    category       keyword  筛选、分组、精确匹配
    goods_id       keyword
    price          double

mapping 建好之后,已有字段的类型就不能改了(新增字段可以)。要改结构只能
新建 goods_v2 再 reindex —— 所以索引名从一开始就带版本号。
"""

from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.helpers import bulk
from flask import current_app

# 商品索引 mapping
GOODS_MAPPING = {
    "mappings": {
        "properties": {
            "title": {
                "type": "text",
                "analyzer": "ik_max_word",       # 写索引:切得最细,提高召回
                "search_analyzer": "ik_smart",   # 查询:智能切分,避免切得过碎
            },
            "desc": {
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_smart",
            },
            "category": {"type": "keyword"},   # keyword:不分词,用于精确匹配 / 过滤
            "goods_id": {"type": "keyword"},
            "price": {"type": "double"},
        }
    }
}

# 写入时用哪个字段当文档 _id(没有这个字段就交给 ES 生成)
ID_FIELD = "goods_id"


class EsStore:
    """封装对 Elasticsearch 的连接,以及索引 / 文档 / 查询 / 分词操作。"""

    def __init__(self, index_name: str | None = None):
        self.index_name = index_name or current_app.config["RAG_SCHEMES"]["graph_rag"]["ES_INDEX"]
        self.client = Elasticsearch(
            hosts=[f"http://{current_app.config['ES_HOST']}:{current_app.config['ES_PORT']}"],
            verify_certs=False,
            request_timeout=60,
        )

    # --- 连通性---

    def ping(self) -> bool:
        """能连通返回 True。

        注意:8.x 客户端把连接异常吞了,连不上是返回 False 而不是抛异常;
        想知道为什么连不上,得用 info()。
        """
        return bool(self.client.ping())

    def info(self) -> dict:
        """集群信息(name / cluster_name / version)。连不上会抛 ConnectionError。"""
        return self.client.info()

    # --- 索引 ---

    def index_exists(self) -> bool:
        return bool(self.client.indices.exists(index=self.index_name))

    def ensure_index(self, mapping: dict | None = None) -> bool:
        """索引不存在时按 mapping 创建(幂等)。

        返回 True 表示这次真的建了,False 表示索引本来就存在。
        """
        if self.index_exists():
            return False
        self.client.indices.create(index=self.index_name, body=mapping or GOODS_MAPPING)
        return True

    def delete_index(self) -> bool:
        """删索引。索引不存在返回 False。"""
        if not self.index_exists():
            return False
        self.client.indices.delete(index=self.index_name)
        return True

    def index_mapping(self) -> dict:
        """读索引的 mapping,用来确认 IK 到底有没有配上。"""
        return self.client.indices.get_mapping(index=self.index_name)[self.index_name]["mappings"]

    def count(self) -> int:
        """索引里的文档条数。"""
        return int(self.client.count(index=self.index_name)["count"])

    def refresh(self) -> None:
        """立刻刷新索引。

        ES 默认 1 秒才把写入变成可搜索(近实时),写完马上查会查不到,
        案例里每次写完刷一下,行为更符合直觉。
        """
        self.client.indices.refresh(index=self.index_name)


    def index_doc(self, doc: dict, doc_id: str | None = None) -> dict:
        """写入单条文档。doc_id 为 None 时由 ES 生成随机 id。"""
        return self.client.index(index=self.index_name, id=doc_id, document=doc)

    def bulk_index(self, docs: list[dict]) -> tuple[int, list[dict]]:
        """bulk 批量写入文档。返回成功条数, 失败明细列表。

        逐条写每次都要一次 HTTP 往返,bulk 把多条合成一个请求。
        每条的 _id 取 doc 里的 goods_id(有的话),这样后面能按 id 取 / 改 / 删。
        """

        def _actions():
            for doc in docs:
                action: dict = {"_index": self.index_name, "_source": doc}
                doc_id = doc.get(ID_FIELD)
                if doc_id is not None:
                    action["_id"] = str(doc_id)
                yield action

        # raise_on_error=False:一条失败不影响整批,失败明细从返回值里拿
        success, errors = bulk(self.client, _actions(), raise_on_error=False)
        return int(success), list(errors)

    def get_doc(self, doc_id: str) -> dict | None:
        """按 _id 取单条文档。不存在返回 None。"""
        try:
            return self.client.get(index=self.index_name, id=doc_id)["_source"]
        except NotFoundError:
            return None

    def update_doc(self, doc_id: str, partial: dict) -> bool:
        """按 _id 局部更新:只传要改的字段。文档不存在返回 False。"""
        try:
            self.client.update(index=self.index_name, id=doc_id, doc=partial)
            return True
        except NotFoundError:
            return False

    def delete_doc(self, doc_id: str) -> bool:
        """按 _id 删文档。文档不存在返回 False。"""
        try:
            self.client.delete(index=self.index_name, id=doc_id)
            return True
        except NotFoundError:
            return False

    # --- 查询与分词 ---

    def search(self, body: dict) -> dict:
        """执行检索。body 是完整的 ES 查询 DSL,由 services 层组装。"""
        return self.client.search(index=self.index_name, body=body)

    def analyze(self, text: str, analyzer: str) -> list[str]:
        """用指定分析器切词,返回 token 列表(不用建索引也能调)。"""
        resp = self.client.indices.analyze(analyzer=analyzer, text=text)
        return [t["token"] for t in resp["tokens"]]
