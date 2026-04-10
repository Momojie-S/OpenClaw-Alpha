"""Milvus 连接管理模块。"""

from pymilvus import MilvusClient

from openclaw_alpha.core.settings import settings

_client: MilvusClient | None = None


def get_client() -> MilvusClient:
    """获取 MilvusClient 单例。

    环境变量:
        MILVUS_URI: Milvus 连接地址
        MILVUS_TOKEN: 认证 token

    Returns:
        pymilvus.MilvusClient 实例

    Raises:
        ValueError: 环境变量未配置
    """
    global _client
    if _client is not None:
        return _client

    uri = settings.milvus_uri
    token = settings.milvus_token

    # Zilliz Serverless URI 需要显式指定 443 端口
    if uri.startswith("https://") and ":" not in uri[8:]:
        uri = uri + ":443"

    _client = MilvusClient(uri=uri, token=token)
    return _client


def close() -> None:
    """关闭 Milvus 连接并重置单例。"""
    global _client
    if _client is not None:
        _client.close()
        _client = None
