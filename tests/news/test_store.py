"""News 存储模块测试。"""

import json
import os
import time
from unittest.mock import MagicMock, patch

import pytest

from openclaw_alpha.news.store import ensure_collection
from openclaw_alpha.news.service import _sync_to_milvus, read_news_json, write_news_json
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
        client.describe_collection.return_value = {
            "fields": [{"name": "entities_vector"}]
        }

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
        client.describe_collection.return_value = {
            "fields": [{"name": "entities_vector"}]
        }

        ensure_collection(client)
        ensure_collection(client)

        client.create_collection.assert_not_called()


class TestSyncToMilvus:
    """_sync_to_milvus 是当前唯一的 Milvus 写入路径。"""

    def _setup_news(self, data_dir, news_id, summary="摘要", event_id="", entities="实体"):
        """辅助：创建 news.json + summary_vector.json。"""
        d = data_dir / "news" / news_id
        d.mkdir(parents=True, exist_ok=True)
        news = {
            "news_id": news_id,
            "title": "测试",
            "summary": summary,
            "entities": entities,
            "event_id": event_id,
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
        }
        (d / "news.json").write_text(json.dumps(news, ensure_ascii=False), encoding="utf-8")
        (d / "summary_vector.json").write_text(
            json.dumps({"vector": [0.1] * 1024}), encoding="utf-8"
        )

    def test_sync_calls_embed_and_upsert(self, tmp_path):
        self._setup_news(tmp_path, "news_1", event_id="evt_1", entities="NVDA 芯片")
        mock_client = MagicMock()
        mock_client.has_collection.return_value = True

        with patch("openclaw_alpha.news.service.get_client", return_value=mock_client):
            _sync_to_milvus("news_1", data_dir=tmp_path)

        mock_client.upsert.assert_called_once()
        data = mock_client.upsert.call_args.kwargs["data"]
        assert len(data) == 1
        assert data[0]["news_id"] == "news_1"
        assert data[0]["entities"] == "NVDA 芯片"
        assert data[0]["event_id"] == "evt_1"
        assert len(data[0]["summary_vector"]) == 1024

    def test_sync_no_event_id(self, tmp_path):
        self._setup_news(tmp_path, "news_2", entities="实体")
        mock_client = MagicMock()
        mock_client.has_collection.return_value = True

        with patch("openclaw_alpha.news.service.get_client", return_value=mock_client):
            _sync_to_milvus("news_2", data_dir=tmp_path)

        data = mock_client.upsert.call_args.kwargs["data"]
        assert data[0]["event_id"] == ""

    def test_sync_no_vector_skips(self, tmp_path):
        """无 summary_vector.json 时跳过同步。"""
        d = tmp_path / "news" / "news_3"
        d.mkdir(parents=True)
        (d / "news.json").write_text(
            json.dumps({"news_id": "news_3", "title": "无向量"}), encoding="utf-8"
        )
        mock_client = MagicMock()

        with patch("openclaw_alpha.news.service.get_client", return_value=mock_client):
            _sync_to_milvus("news_3", data_dir=tmp_path)

        mock_client.upsert.assert_not_called()

    def test_sync_news_not_found(self, tmp_path):
        """news_id 不存在时静默跳过。"""
        mock_client = MagicMock()

        with patch("openclaw_alpha.news.service.get_client", return_value=mock_client):
            _sync_to_milvus("nonexistent", data_dir=tmp_path)

        mock_client.upsert.assert_not_called()
