"""Embedding 向量生成服务。"""

from openclaw_alpha.core.embedding.base import Embedder
from openclaw_alpha.core.embedding.factory import get_embedder

__all__ = ["Embedder", "get_embedder"]
