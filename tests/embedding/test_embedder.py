"""Embedding 模块测试。"""

import os
from unittest.mock import MagicMock, patch

import pytest

from openclaw_alpha.core.embedding.factory import _reset, get_embedder
from openclaw_alpha.core.embedding.dashscope import DashScopeEmbedder


@pytest.fixture(autouse=True)
def _reset_embedder():
    _reset()
    yield
    _reset()


class TestFactory:
    def test_dashscope_when_key_set(self, monkeypatch):
        monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")

        embedder = get_embedder()
        assert isinstance(embedder, DashScopeEmbedder)
        # 单例
        assert get_embedder() is embedder

    def test_no_key_raises(self, monkeypatch):
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)

        with pytest.raises(ValueError, match="DASHSCOPE_API_KEY"):
            get_embedder()


class TestDashScopeEmbed:
    def test_embed_returns_vector(self):
        embedder = DashScopeEmbedder("test-key")

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"embedding": [0.1] * 1024}]}
        mock_resp.raise_for_status = MagicMock()

        with patch("openclaw_alpha.core.embedding.dashscope.httpx.post", return_value=mock_resp):
            vec = embedder.embed("测试文本")

        assert len(vec) == 1024
        assert vec[0] == 0.1

    def test_embed_api_error(self):
        embedder = DashScopeEmbedder("test-key")

        with patch("openclaw_alpha.core.embedding.dashscope.httpx.post") as mock_post:
            mock_post.return_value.raise_for_status.side_effect = Exception("API Error")

            with pytest.raises(Exception, match="API Error"):
                embedder.embed("测试")
