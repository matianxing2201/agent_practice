"""Parent-Document RAG 方案:父子分块,小块检索、大块返回。

解决的问题:单层分块的两难——切大块检索不准,切小块语义残缺。
解法:双层表示——子块(小)存向量库负责「检索」,父块(大)存 KV 负责「上下文」;
命中子块后回取父块全文交给 LLM,解决「切片切碎语义」问题。

参考 4_parent_document_rag,索引与检索全部自包含在本方案内
(只复用 knowledge_base 的向量化组件),knowledge_base 保持单层 CRUD 纯粹。
"""

from .. import bp
from . import controllers  # noqa: F401  导入即注册路由到 rag 蓝图
