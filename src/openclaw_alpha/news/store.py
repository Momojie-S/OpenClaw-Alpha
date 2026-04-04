"""新闻条目 Milvus 存储实现。"""

import time

from pymilvus import CollectionSchema, DataType, FieldSchema, MilvusClient

from openclaw_alpha.core.embedding import get_embedder
from openclaw_alpha.core.milvus import get_client

_COLLECTION = "news_items"
_DIM = 1024


def ensure_collection(client: MilvusClient) -> None:
    """确保 news_items collection 存在，不存在则创建。"""
    if client.has_collection(_COLLECTION):
        return

    schema = CollectionSchema(fields=[
        FieldSchema("news_id", DataType.VARCHAR, is_primary=True, max_length=256),
        FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=_DIM),
        FieldSchema("event_id", DataType.VARCHAR, max_length=256),
        FieldSchema("entities", DataType.VARCHAR, max_length=2048),
        FieldSchema("created_at", DataType.INT64),
    ])

    index_params = client.prepare_index_params()
    index_params.add_index(field_name="embedding", index_type="AUTOINDEX", metric_type="COSINE")
    index_params.add_index(
        field_name="entities",
        index_type="INVERTED",
        params={"enable_analyzer": True, "analyzer_params": {"type": "jieba"}},
    )

    client.create_collection(
        collection_name=_COLLECTION,
        schema=schema,
        index_params=index_params,
    )


def insert_news(
    news_id: str,
    text: str,
    entities: str,
    event_id: str | None = None,
) -> None:
    """插入一条新闻到 Milvus。

    Args:
        news_id: 新闻唯一标识
        text: 新闻摘要/标题（用于生成 embedding）
        entities: 实体词，空格分隔
        event_id: 所属事件ID，可选
    """
    client = get_client()
    ensure_collection(client)

    embedder = get_embedder()
    vector = embedder.embed(text)

    client.insert(
        collection_name=_COLLECTION,
        data=[{
            "news_id": news_id,
            "embedding": vector,
            "event_id": event_id or "",
            "entities": entities,
            "created_at": int(time.time()),
        }],
    )
