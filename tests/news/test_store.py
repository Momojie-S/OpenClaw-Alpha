"""News 存储模块测试。"""

import os
from unittest.mock import MagicMock, patch

import pytest

from openclaw_alpha.news.store import ensure_collection, insert_news
from openclaw_alpha.core.embedding.factory import _reset


@pytest.fixture(autouse=True)
def _reset_embedder():
    _reset()
    yield
    _reset()


class TestEnsureCollection:
    def test_exists_skip(self):
        client = MagicMock()
        client.has_collection.return_value = True

        ensure_collection(client)

        client.create_collection.assert_not_called()

    def test_not_exists_create(self):
        client = MagicMock()
        client.has_collection.return_value = False
        client.prepare_index_params.return_value = MagicMock()

        ensure_collection(client)

        client.create_collection.assert_called_once()
        call_kwargs = client.create_collection.call_args
        assert call_kwargs.kwargs["collection_name"] == "news_items"

    def test_idempotent(self):
        client = MagicMock()
        client.has_collection.return_value = True

        ensure_collection(client)
        ensure_collection(client)

        client.create_collection.assert_not_called()


class TestInsertNews:
    def test_insert_calls_embed_and_insert(self, monkeypatch):
        mock_client = MagicMock()
        mock_client.has_collection.return_value = True

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.1] * 1024

        with (
            patch("openclaw_alpha.news.store.get_client", return_value=mock_client),
            patch("openclaw_alpha.news.store.get_embedder", return_value=mock_embedder),
        ):
            insert_news("news_1", "测试标题", "NVDA 芯片", event_id="evt_1")

        mock_embedder.embed.assert_called_once_with("测试标题")
        mock_client.insert.assert_called_once()

        data = mock_client.insert.call_args.kwargs["data"]
        assert len(data) == 1
        assert data[0]["news_id"] == "news_1"
        assert data[0]["entities"] == "NVDA 芯片"
        assert data[0]["event_id"] == "evt_1"
        assert len(data[0]["embedding"]) == 1024

    def test_insert_no_event_id(self, monkeypatch):
        mock_client = MagicMock()
        mock_client.has_collection.return_value = True

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.0] * 1024

        with (
            patch("openclaw_alpha.news.store.get_client", return_value=mock_client),
            patch("openclaw_alpha.news.store.get_embedder", return_value=mock_embedder),
        ):
            insert_news("news_2", "标题", "实体")

        data = mock_client.insert.call_args.kwargs["data"]
        assert data[0]["event_id"] == ""


@pytest.mark.skipif(
    not os.environ.get("MILVUS_URI") or not os.environ.get("DASHSCOPE_API_KEY"),
    reason="需要 .env 中配置 MILVUS_URI 和 DASHSCOPE_API_KEY",
)
class TestRealConnection:
    """真实连接测试：创建 collection + 插入 + 搜索。"""

    def test_insert_and_search(self):
        from openclaw_alpha.core.milvus import get_client

        insert_news(
            news_id="test_news_001",
            text="测试新闻条目用于验证存储功能",
            entities="测试 验证",
        )

        client = get_client()
        results = client.search(
            collection_name="news_items",
            data=[[0.0] * 1024],  # dummy vector just to verify search works
            limit=1,
            output_fields=["news_id", "entities"],
        )
        assert len(results) > 0

        # cleanup
        client.delete(collection_name="news_items", filter='news_id == "test_news_001"')
