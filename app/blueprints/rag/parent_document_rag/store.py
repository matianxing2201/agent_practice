"""双层存储:子块 -> Milvus(向量检索),父块 -> JSON 文件(KV 精确取)。

两种存储对应两种查询(教学核心):
    子块存向量库 —— 回答「哪个片段跟问题最像?」用向量相似度找;
    父块存 KV    —— 回答「这个 id 的全文是什么?」按 parent_id 精确取。

生产环境父块 KV 会用 Redis 等服务,这里用 JSON 文件 + dict 演示同一抽象:
    文件路径:knowledge_base/parent_chunks_{collection}.json(gitignored 私有数据区)
    结构:{"parent_id": "全文", ...}
"""

import json
import os

from flask import current_app
from pymilvus import DataType, MilvusClient


class ChildStore:
    """子块向量库(Milvus):schema 比单层知识库多一个 parent_id 指针字段。"""

    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.client = MilvusClient(
            uri=f"http://{current_app.config['MILVUS_HOST']}:{current_app.config['MILVUS_PORT']}"
        )

    def ensure_collection(self) -> None:
        if self.client.has_collection(self.collection_name):
            return
        schema = self.client.create_schema(auto_id=True, enable_dynamic_field=False)
        schema.add_field("id", DataType.INT64, is_primary=True)
        schema.add_field("vector", DataType.FLOAT_VECTOR, dim=current_app.config["EMBEDDING_DIM"])
        schema.add_field("text", DataType.VARCHAR, max_length=65535)
        schema.add_field("parent_id", DataType.VARCHAR, max_length=100)
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            metric_type=current_app.config["METRIC_TYPE"],
            index_type="AUTOINDEX",
        )
        self.client.create_collection(
            self.collection_name, schema=schema, index_params=index_params
        )

    def insert_children(self, rows: list[dict]) -> int:
        """批量写入子块(id 由 Milvus 自动分配),flush 保证立即可查。"""
        self.ensure_collection()
        self.client.insert(self.collection_name, data=rows)
        self.client.flush(self.collection_name)
        return len(rows)

    def search(self, query_vector: list[float], top_k: int) -> list[dict]:
        """向量检索子块,返回命中的 {text, parent_id, score}。"""
        self.ensure_collection()
        results = self.client.search(
            collection_name=self.collection_name,
            data=[query_vector],
            limit=top_k,
            output_fields=["text", "parent_id"],
        )
        return [
            {
                "text": r["entity"]["text"],
                "parent_id": r["entity"]["parent_id"],
                "score": r["distance"],
            }
            for r in results[0]
        ]


class ParentStore:
    """父块 KV 存储:JSON 文件 + dict(parent_id -> 全文)。"""

    def __init__(self, collection_name: str):
        self._file = os.path.join(
            current_app.config["KNOWLEDGE_BASE_DIR"],
            f"parent_chunks_{collection_name}.json",
        )

    def _load(self) -> dict:
        if not os.path.exists(self._file):
            return {}
        with open(self._file, encoding="utf-8") as f:
            return json.load(f)

    def save_many(self, parents: dict[str, str]) -> None:
        """追加父块(与 knowledge_base 的累积式导入语义一致)。"""
        data = self._load()
        data.update(parents)
        os.makedirs(os.path.dirname(self._file), exist_ok=True)
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_many(self, parent_ids: list[str]) -> list[dict]:
        """按入参顺序取父块全文(跳过不存在的 id),供拼接上下文。"""
        data = self._load()
        return [
            {"parent_id": pid, "text": data[pid]}
            for pid in parent_ids
            if pid in data
        ]
