"""Milvus 数据访问层:知识库 CRUD 的增删改查。

collection schema(三条记录各为一个字段):
    id      INT64  主键(应用分配,递增)
    vector  FLOAT_VECTOR  2048 维
    text    VARCHAR  原文

id 由应用分配而非 Milvus auto_id:auto_id 的 collection 无法用原 id 更新记录
(upsert 会重新生成 id),应用分配才能满足 Update 保持 id 不变。
"""

from flask import current_app
from pymilvus import DataType, MilvusClient


class MilvusStore:
    """封装对知识库 collection 的增删改查。"""

    def __init__(self, collection_name: str, uri: str | None = None):
        self.collection_name = collection_name
        self.client = MilvusClient(
            uri=uri or f"http://{current_app.config['MILVUS_HOST']}:{current_app.config['MILVUS_PORT']}"
        )

    def ensure_collection(self) -> None:
        """collection 不存在时创建(幂等)。"""
        if self.client.has_collection(self.collection_name):
            return
        schema = self.client.create_schema(auto_id=False, enable_dynamic_field=False)
        schema.add_field("id", DataType.INT64, is_primary=True)
        schema.add_field("vector", DataType.FLOAT_VECTOR, dim=current_app.config["EMBEDDING_DIM"])
        schema.add_field("text", DataType.VARCHAR, max_length=65535)
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            metric_type=current_app.config["METRIC_TYPE"],
            index_type="AUTOINDEX",
        )
        self.client.create_collection(
            self.collection_name, schema=schema, index_params=index_params
        )

    def _next_ids(self, n: int) -> list[int]:
        """分配 n 个连续递增 id(当前最大 id + 1 起)。

        Milvus 不支持 max(id) 聚合,知识库数据量小,直接拉取全部 id 求最大值。
        """
        self.ensure_collection()
        rows = self.client.query(
            self.collection_name,
            filter="id >= 0",
            output_fields=["id"],
            limit=16384,
            consistency_level="Strong",
        )
        current_max = max(r["id"] for r in rows) if rows else 0
        return list(range(current_max + 1, current_max + 1 + n))

    def insert(self, texts: list[str], vectors: list[list[float]]) -> list[int]:
        """批量写入记录,返回分配的 id 列表。flush 保证写入立即可查。"""
        self.ensure_collection()
        ids = self._next_ids(len(texts))
        rows = [
            {"id": i, "vector": v, "text": t}
            for i, t, v in zip(ids, texts, vectors)
        ]
        self.client.insert(self.collection_name, data=rows)
        self.client.flush(self.collection_name)
        return ids

    def get(self, record_id: int) -> dict | None:
        """按 id 查询单条记录,不存在返回 None。"""
        self.ensure_collection()
        rows = self.client.query(
            self.collection_name,
            filter=f"id == {record_id}",
            output_fields=["id", "text"],
            consistency_level="Strong",
        )
        return rows[0] if rows else None

    def update(self, record_id: int, text: str, vector: list[float]) -> bool:
        """按 id 更新 text 与 vector(id 不变)。记录不存在返回 False。"""
        if self.get(record_id) is None:
            return False
        self.client.upsert(
            self.collection_name,
            data=[{"id": record_id, "vector": vector, "text": text}],
        )
        self.client.flush(self.collection_name)
        return True

    def delete(self, record_id: int) -> bool:
        """按 id 删除记录。记录不存在返回 False。"""
        if self.get(record_id) is None:
            return False
        self.client.delete(self.collection_name, filter=f"id == {record_id}")
        self.client.flush(self.collection_name)
        return True

    def list_records(self, page: int, size: int) -> tuple[list[dict], int]:
        """分页查询全部记录,返回 (items, total)。"""
        self.ensure_collection()
        offset = (page - 1) * size
        items = self.client.query(
            self.collection_name,
            filter="id >= 0",
            output_fields=["id", "text"],
            limit=size,
            offset=offset,
            consistency_level="Strong",
        )
        total = self.client.query(
            self.collection_name,
            filter="id >= 0",
            output_fields=["count(*)"],
            consistency_level="Strong",
        )[0]["count(*)"]
        return items, total
