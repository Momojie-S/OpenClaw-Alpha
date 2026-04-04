# -*- coding: utf-8 -*-
"""News Fetcher 测试"""

import pytest
from unittest.mock import MagicMock, patch

from openclaw_alpha.news.fetcher import fetch, NewsItem, NewsResult
from openclaw_alpha.news.fetcher.akshare_impl import NewsFetcherAkshare
from openclaw_alpha.news.fetcher.rsshub_impl import NewsFetcherRsshub
from openclaw_alpha.news.fetcher.news_fetcher import NewsFetcherCls


class TestNewsIdGeneration:
    """测试 news_id 生成逻辑"""

    def test_rsshub_news_id(self):
        assert NewsFetcherRsshub.generate_news_id("cls", "abc123") == "cls_abc123"

    def test_rsshub_news_id_route_extraction(self):
        # route_id 为路由第一段
        assert NewsFetcherRsshub.generate_news_id("jin10", "xyz") == "jin10_xyz"

    def test_akshare_news_id_deterministic(self):
        id1 = NewsFetcherAkshare.generate_news_id("cls_global", "标题", "2026-04-04", "10:00:00")
        id2 = NewsFetcherAkshare.generate_news_id("cls_global", "标题", "2026-04-04", "10:00:00")
        assert id1 == id2

    def test_akshare_news_id_format(self):
        news_id = NewsFetcherAkshare.generate_news_id("stock", "标题", "2026-04-04", "10:00:00")
        assert news_id.startswith("stock_")
        # md5[:12] = 12 hex chars
        parts = news_id.split("_", 1)
        assert len(parts[1]) == 12

    def test_akshare_different_content_different_id(self):
        id1 = NewsFetcherAkshare.generate_news_id("s", "标题A", "2026-04-04", "")
        id2 = NewsFetcherAkshare.generate_news_id("s", "标题B", "2026-04-04", "")
        assert id1 != id2


class TestPriorityFallback:
    """测试优先级回退逻辑"""

    @pytest.mark.asyncio
    async def test_unsupported_source_fallback(self):
        """AKShare 不支持的 source 应回退到 RSSHub"""
        fetcher = NewsFetcherCls()

        # mock RSSHub 返回结果
        mock_item = MagicMock()
        mock_item.id = "test123"
        mock_item.title = "测试"
        mock_item.summary = "内容"
        mock_item.published = "2026-04-04T10:00:00+08:00"
        mock_item.link = "https://example.com"

        with patch(
            "openclaw_alpha.news.fetcher.rsshub_impl.async_fetch_with_fallback",
            return_value=("instance.com", [mock_item])
        ):
            result = await fetcher.fetch(source="cls_telegraph", limit=10)
            assert result.total == 1
            assert result.news[0].news_id == "cls_test123"


class TestIntegration:
    """集成测试：真实调用"""

    @pytest.mark.asyncio
    async def test_rsshub_real_fetch(self):
        """真实调用 RSSHub，验证返回结构"""
        result = await fetch(source="cls_telegraph", limit=3)

        assert result.total > 0
        assert result.source.startswith("RSSHub")

        for item in result.news:
            assert item.news_id.startswith("cls_")
            assert len(item.news_id) > 4  # cls_ + 至少1字符
            assert item.title  # 标题非空
