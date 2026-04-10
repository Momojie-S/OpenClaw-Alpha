"""Embedding 工厂：按环境变量自动选择实现。"""

from typing import Union

from openclaw_alpha.core.embedding.base import Embedder
from openclaw_alpha.core.settings import settings

_embedder: Embedder | None = None


def get_embedder() -> Embedder:
    """获取 Embedder 单例，按环境变量自动选择实现。

    Returns:
        Embedder 实例

    Raises:
        ValueError: 未配置任何 embedding 服务
    """
    global _embedder
    if _embedder is not None:
        return _embedder

    api_key = settings.dashscope_api_key
    if api_key:
        from openclaw_alpha.core.embedding.dashscope import DashScopeEmbedder

        _embedder = DashScopeEmbedder(api_key)
        return _embedder

    raise ValueError("未配置 embedding 服务 API Key（需要 DASHSCOPE_API_KEY）")

def _reset() -> None:
    """重置单例（仅供测试使用）。"""
    global _embedder
    _embedder = None
