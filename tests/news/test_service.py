# -*- coding: utf-8 -*-
"""News service 单元测试。"""

import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from openclaw_alpha.news.service import (
    fetch_and_save,
    update_news,
    search_similar,
    search_keyword,
    get_news,
    get_event,
    read_news_json,
    write_news_json,
    _build_entities,
    _save_news_item,
)
from openclaw_alpha.news.fetcher.models import NewsItem


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path


def _create_news(data_dir: Path, news_id: str, extra: dict | None = None):
    """辅助：创建一个 news.json。"""
    d = data_dir / "news" / news_id
    d.mkdir(parents=True, exist_ok=True)
    news = {
        "news_id": news_id,
        "title": "测试",
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
    }
    if extra:
        news.update(extra)
    (d / "news.json").write_text(json.dumps(news, ensure_ascii=False), encoding="utf-8")
    return news


class TestBuildEntities:
    def test_sectors_and_companies(self):
        analysis = {
            "related_sectors": ["AI", "半导体"],
            "related_companies": [{"name": "NVDA", "listed": True}],
        }
        assert _build_entities(analysis) == "AI 半导体 NVDA"

    def test_empty(self):
        assert _build_entities({}) == ""


class TestFetchAndSave:
    @pytest.mark.asyncio
    async def test_saves_new_items(self, data_dir, tmp_path):
        items = [
            NewsItem(news_id="cls_001", title="新闻1", content="内容1", date="2026-04-04"),
            NewsItem(news_id="cls_002", title="新闻2", content="内容2", date="2026-04-04"),
        ]
        mock_result = MagicMock()
        mock_result.news = items
        mock_result.source = "RSSHub_cls"
        mock_result.total = 2

        with patch("openclaw_alpha.news.service.fetcher_fetch", return_value=mock_result):
            result = await fetch_and_save(source="cls_telegraph", data_dir=data_dir)

        assert result["saved"] == 2
        assert result["skipped"] == 0
        assert (data_dir / "news" / "cls_001" / "news.json").exists()
        assert (data_dir / "news" / "cls_001" / "content.md").exists()

    @pytest.mark.asyncio
    async def test_idempotent_skip(self, data_dir):
        _create_news(data_dir, "cls_001")
        items = [NewsItem(news_id="cls_001", title="新", content="x", date="2026-04-04")]
        mock_result = MagicMock()
        mock_result.news = items
        mock_result.source = "RSSHub_cls"
        mock_result.total = 1

        with patch("openclaw_alpha.news.service.fetcher_fetch", return_value=mock_result):
            result = await fetch_and_save(data_dir=data_dir)

        assert result["saved"] == 0
        assert result["skipped"] == 1

    @pytest.mark.asyncio
    async def test_idempotent_no_overwrite(self, data_dir):
        """幂等调用不覆盖已有内容。"""
        original = _create_news(data_dir, "cls_001", {"title": "原标题", "summary": "原摘要"})

        items = [NewsItem(news_id="cls_001", title="新标题", content="新内容", date="2026-04-04")]
        mock_result = MagicMock()
        mock_result.news = items
        mock_result.source = "RSSHub_cls"
        mock_result.total = 1

        with patch("openclaw_alpha.news.service.fetcher_fetch", return_value=mock_result):
            await fetch_and_save(data_dir=data_dir)

        # 原始数据不变
        news = read_news_json("cls_001", data_dir=data_dir)
        assert news["title"] == "原标题"
        assert news["summary"] == "原摘要"

    @pytest.mark.asyncio
    async def test_mixed_new_and_existing(self, data_dir):
        """部分新、部分已存在。"""
        _create_news(data_dir, "cls_001")

        items = [
            NewsItem(news_id="cls_001", title="旧新闻", content="x", date="2026-04-04"),
            NewsItem(news_id="cls_002", title="新新闻", content="y", date="2026-04-04"),
        ]
        mock_result = MagicMock()
        mock_result.news = items
        mock_result.source = "RSSHub_cls"
        mock_result.total = 2

        with patch("openclaw_alpha.news.service.fetcher_fetch", return_value=mock_result):
            result = await fetch_and_save(data_dir=data_dir)

        assert result["saved"] == 1
        assert result["skipped"] == 1
        assert result["news"][0]["news_id"] == "cls_001"
        assert result["news"][1]["news_id"] == "cls_002"


class TestUpdateNews:
    def test_not_found(self, data_dir):
        result = update_news("nonexistent", data_dir=data_dir)
        assert "error" in result

    def test_update_summary(self, data_dir):
        _create_news(data_dir, "cls_001")
        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.1] * 1024

        with patch("openclaw_alpha.news.service.get_embedder", return_value=mock_embedder), \
             patch("openclaw_alpha.news.service._sync_to_milvus"):
            result = update_news("cls_001", summary="新摘要", data_dir=data_dir)

        assert result["updated"] is True
        news = json.loads((data_dir / "news" / "cls_001" / "news.json").read_text())
        assert news["summary"] == "新摘要"
        emb = json.loads((data_dir / "news" / "cls_001" / "embedding.json").read_text())
        assert len(emb["vector"]) == 1024

    def test_update_analysis(self, data_dir):
        _create_news(data_dir, "cls_001")
        analysis = {
            "related_sectors": ["AI"],
            "related_companies": [{"name": "NVDA", "listed": True, "code": "000001"}],
            "worth_deep_analysis": False,
        }

        with patch("openclaw_alpha.news.service._sync_to_milvus"):
            result = update_news("cls_001", analysis=analysis, data_dir=data_dir)

        news = json.loads((data_dir / "news" / "cls_001" / "news.json").read_text())
        assert news["entities"] == "AI NVDA"

    def test_update_all_at_once(self, data_dir):
        _create_news(data_dir, "cls_001")
        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.1] * 1024
        analysis = {"related_sectors": ["芯片"], "related_companies": [], "worth_deep_analysis": True}

        with patch("openclaw_alpha.news.service.get_embedder", return_value=mock_embedder), \
             patch("openclaw_alpha.news.service._sync_to_milvus") as mock_sync:
            update_news("cls_001", summary="s", analysis=analysis, event_id="evt_1", data_dir=data_dir)

        mock_sync.assert_called_once()


class TestSearchSimilar:
    def test_not_found(self, data_dir):
        result = search_similar("nonexistent", data_dir=data_dir)
        assert "error" in result

    def test_no_embedding(self, data_dir):
        _create_news(data_dir, "cls_001")
        result = search_similar("cls_001", data_dir=data_dir)
        assert "error" in result
        assert "no embedding" in result["error"]


class TestGetNews:
    def test_not_found(self, data_dir):
        result = get_news("nonexistent", data_dir=data_dir)
        assert "error" in result

    def test_all_fields(self, data_dir):
        _create_news(data_dir, "cls_001", {"summary": "摘要"})
        result = get_news("cls_001", data_dir=data_dir)
        assert result["summary"] == "摘要"

    def test_specific_fields(self, data_dir):
        _create_news(data_dir, "cls_001", {"summary": "摘要", "title": "标题"})
        result = get_news("cls_001", fields=["summary"], data_dir=data_dir)
        assert result == {"summary": "摘要"}

    def test_content_field(self, data_dir):
        _create_news(data_dir, "cls_001")
        (data_dir / "news" / "cls_001" / "content.md").write_text("原文", encoding="utf-8")
        result = get_news("cls_001", fields=["content"], data_dir=data_dir)
        assert result == {"content": "原文"}


class TestGetEvent:
    def test_not_found(self, data_dir):
        result = get_event("nonexistent", data_dir=data_dir)
        assert "error" in result

    def test_found(self, data_dir):
        d = data_dir / "events" / "evt_001"
        d.mkdir(parents=True)
        (d / "event.json").write_text('{"event_id":"evt_001","summary":"事件"}', encoding="utf-8")
        result = get_event("evt_001", data_dir=data_dir)
        assert result["event_id"] == "evt_001"


class TestAnalysisStatus:
    """analysis_status 状态追踪测试。"""

    def test_new_news_no_analysis_status(self, data_dir):
        """新落盘的新闻不应有 analysis_status 字段。"""
        _create_news(data_dir, "cls_001")
        news = read_news_json("cls_001", data_dir=data_dir)
        assert "analysis_status" not in news

    def test_set_pending(self, data_dir):
        """Backend 写入 pending。"""
        _create_news(data_dir, "cls_001")
        news = read_news_json("cls_001", data_dir=data_dir)
        news["analysis_status"] = "pending"
        write_news_json("cls_001", news, data_dir=data_dir)
        news = read_news_json("cls_001", data_dir=data_dir)
        assert news["analysis_status"] == "pending"

    def test_set_done(self, data_dir):
        """Backend 写入 done + worth_deep_analysis。"""
        _create_news(data_dir, "cls_001")
        news = read_news_json("cls_001", data_dir=data_dir)
        news["analysis_status"] = "done"
        news["worth_deep_analysis"] = True
        write_news_json("cls_001", news, data_dir=data_dir)
        news = read_news_json("cls_001", data_dir=data_dir)
        assert news["analysis_status"] == "done"
        assert news["worth_deep_analysis"] is True

    def test_set_failed(self, data_dir):
        """Backend 写入 failed。"""
        _create_news(data_dir, "cls_001")
        news = read_news_json("cls_001", data_dir=data_dir)
        news["analysis_status"] = "failed"
        write_news_json("cls_001", news, data_dir=data_dir)
        news = read_news_json("cls_001", data_dir=data_dir)
        assert news["analysis_status"] == "failed"

    def test_scan_pending(self, data_dir):
        """扫描待分析新闻：无 status 或 failed。"""
        _create_news(data_dir, "cls_001")  # 无 status → 待分析
        _create_news(data_dir, "cls_002", {"analysis_status": "pending"})  # pending → 跳过
        _create_news(data_dir, "cls_003", {"analysis_status": "done"})  # done → 跳过
        _create_news(data_dir, "cls_004", {"analysis_status": "failed"})  # failed → 可重试

        from openclaw_alpha.backend.quick_news.jobs import _scan_pending_news
        pending = _scan_pending_news(data_dir=data_dir)
        ids = [n["news_id"] for n in pending]
        assert "cls_001" in ids
        assert "cls_002" not in ids
        assert "cls_003" not in ids
        assert "cls_004" in ids

    def test_old_data_compatible(self, data_dir):
        """旧数据（无 analysis_status）能正常被识别为待分析。"""
        _create_news(data_dir, "old_news_001")
        news = read_news_json("old_news_001", data_dir=data_dir)
        assert "analysis_status" not in news
        # 旧数据应该被当作待分析
        from openclaw_alpha.backend.quick_news.jobs import _scan_pending_news
        pending = _scan_pending_news(data_dir=data_dir)
        assert any(n["news_id"] == "old_news_001" for n in pending)
