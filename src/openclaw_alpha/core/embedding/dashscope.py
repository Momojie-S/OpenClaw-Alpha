"""DashScope Embedding 实现（text-embedding-v4, 1024d）。"""

import httpx

from openclaw_alpha.core.embedding.base import Embedder

_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
_MODEL = "text-embedding-v4"


class DashScopeEmbedder(Embedder):
    """基于百炼 DashScope 的向量生成器。"""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def embed(self, text: str) -> list[float]:
        resp = httpx.post(
            _API_URL,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={"model": _MODEL, "input": text},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["data"][0]["embedding"]
