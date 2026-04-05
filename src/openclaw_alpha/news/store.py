"""新闻条目 Milvus 存储实现。"""

import time

from pymilvus import (
    CollectionSchema,
    DataType,
    FieldSchema,
    Function,
    FunctionType,
    MilvusClient,
)

from openclaw_alpha.core.milvus import get_client

_COLLECTION = "news_items"
_DIM = 1024


def _build_schema() -> CollectionSchema:
    """构建 news_items collection schema（含 BM25）。"""
    schema = CollectionSchema(fields=[
        FieldSchema("news_id", DataType.VARCHAR, is_primary=True, max_length=256),
        FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=_DIM),
        FieldSchema("bm25_vector", DataType.SPARSE_FLOAT_VECTOR),
        FieldSchema("event_id", DataType.VARCHAR, max_length=256),
        FieldSchema("entities", DataType.VARCHAR, max_length=2048,
                    enable_analyzer=True, analyzer_params={"type": "jieba"}),
        FieldSchema("created_at", DataType.INT64),
    ])

    # BM25 Function: entities → bm25_vector
    schema.add_function(Function(
        name="bm25_entities",
        input_field_names=["entities"],
        output_field_names=["bm25_vector"],
        function_type=FunctionType.BM25,
    ))

    return schema


def _build_index_params(client: MilvusClient):
    """构建索引参数。"""
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        index_type="AUTOINDEX",
        metric_type="COSINE",
    )
    index_params.add_index(
        field_name="bm25_vector",
        index_type="SPARSE_INVERTED_INDEX",
        metric_type="BM25",
    )
    return index_params


def ensure_collection(client: MilvusClient) -> None:
    """确保 news_items collection 存在且 schema 匹配。

    开发阶段：如果已有 collection 缺 bm25_vector 字段，drop + 重建。
    """
    if client.has_collection(_COLLECTION):
        # 检查是否有 bm25_vector 字段
        info = client.describe_collection(_COLLECTION)
        field_names = {f["name"] for f in info.get("fields", [])}
        if "bm25_vector" not in field_names:
            client.drop_collection(_COLLECTION)
        else:
            return

    schema = _build_schema()
    index_params = _build_index_params(client)

    client.create_collection(
        collection_name=_COLLECTION,
        schema=schema,
        index_params=index_params,
    )
