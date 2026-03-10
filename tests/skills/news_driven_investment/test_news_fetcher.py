# -*- coding: utf-8 -*-
"""新闻驱动投资 Fetcher 测试"""

import pytest
from unittest.mock import AsyncMock, patch
import pandas as pd

from openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher import (
    NewsFetcherCls,
    NewsFetcherAkshare,
    NewsItem,
    NewsResult,
    fetch,
)


class TestNewsModels:
    """数据模型测试"""

    def test_news_item_creation(self):
        """NewsItem 创建"""
        item = NewsItem(
            title="测试标题",
            content="测试内容",
            date="2026-03-07",
            time="10:30:00",
            source="财联社",
            url="https://example.com",
        )

        assert item.title == "测试标题"
        assert item.content == "测试内容"
        assert item.date == "2026-03-07"
        assert item.time == "10:30:00"
        assert item.source == "财联社"
        assert item.url == "https://example.com"

    def test_news_item_optional_fields(self):
        """NewsItem 可选字段"""
        item = NewsItem(
            title="标题",
            content="内容",
            date="2026-03-07",
        )

        assert item.time is None
        assert item.source is None
        assert item.url is None

    def test_news_result_creation(self):
        """NewsResult 创建"""
        items = [
            NewsItem(title="新闻1", content="内容1", date="2026-03-07"),
            NewsItem(title="新闻2", content="内容2", date="2026-03-07"),
        ]

        result = NewsResult(news=items, total=2, source="财联社")

        assert len(result.news) == 2
        assert result.total == 2
        assert result.source == "财联社"

    def test_news_result_default_values(self):
        """NewsResult 默认值"""
        result = NewsResult()

        assert result.news == []
        assert result.total == 0
        assert result.source == ""


class TestNewsFetcherAkshareFilter:
    """NewsFetcherAkshare 筛选逻辑测试"""

    @pytest.fixture
    def fetcher(self):
        return NewsFetcherAkshare()

    @pytest.fixture
    def sample_news(self):
        return [
            NewsItem(
                title="AI芯片需求暴增",
                content="英伟达发布新一代AI芯片，算力提升3倍",
                date="2026-03-07",
                source="财联社",
            ),
            NewsItem(
                title="新能源板块大涨",
                content="光伏、储能板块集体走强",
                date="2026-03-07",
                source="财联社",
            ),
            NewsItem(
                title="AI应用落地加速",
                content="多行业AI应用场景拓展，算力需求持续增长",
                date="2026-03-06",
                source="财联社",
            ),
            NewsItem(
                title="半导体行业复苏",
                content="芯片库存去化完成，行业景气度回升",
                date="2026-03-06",
                source="财联社",
            ),
        ]

    # ============== 关键词筛选测试 ==============

    def test_filter_by_keyword_in_title(self, fetcher, sample_news):
        """标题关键词筛选"""
        result = fetcher._filter_news(sample_news, keyword="AI")

        assert len(result) == 2
        assert "AI" in result[0].title
        assert "AI" in result[1].title

    def test_filter_by_keyword_in_content(self, fetcher, sample_news):
        """内容关键词筛选"""
        result = fetcher._filter_news(sample_news, keyword="算力")

        assert len(result) == 2
        assert "算力" in result[0].content or "算力" in result[1].content

    def test_filter_by_keyword_case_insensitive(self, fetcher, sample_news):
        """关键词不区分大小写"""
        result = fetcher._filter_news(sample_news, keyword="ai")

        assert len(result) == 2

    def test_filter_by_keyword_no_match(self, fetcher, sample_news):
        """无匹配关键词"""
        result = fetcher._filter_news(sample_news, keyword="医药")

        assert len(result) == 0

    # ============== 日期筛选测试 ==============

    def test_filter_by_date(self, fetcher, sample_news):
        """日期筛选"""
        result = fetcher._filter_news(sample_news, date="2026-03-07")

        assert len(result) == 2
        for item in result:
            assert "2026-03-07" in str(item.date)

    def test_filter_by_date_no_match(self, fetcher, sample_news):
        """无匹配日期"""
        result = fetcher._filter_news(sample_news, date="2026-03-05")

        assert len(result) == 0

    # ============== 组合筛选测试 ==============

    def test_filter_by_keyword_and_date(self, fetcher, sample_news):
        """关键词 + 日期筛选"""
        result = fetcher._filter_news(
            sample_news,
            keyword="AI",
            date="2026-03-07"
        )

        assert len(result) == 1
        assert result[0].title == "AI芯片需求暴增"

    def test_filter_no_conditions(self, fetcher, sample_news):
        """无筛选条件"""
        result = fetcher._filter_news(sample_news)

        assert len(result) == 4

    # ============== 日期匹配测试 ==============

    def test_match_date_string(self, fetcher):
        """日期字符串匹配"""
        assert fetcher._match_date("2026-03-07", "2026-03-07") is True
        assert fetcher._match_date("2026-03-06", "2026-03-07") is False

    def test_match_date_prefix(self, fetcher):
        """日期前缀匹配（datetime.date 对象会转成字符串）"""
        assert fetcher._match_date("2026-03-07 10:30:00", "2026-03-07") is True
        assert fetcher._match_date("2026-03-07", "2026-03-07") is True

    def test_match_date_object(self, fetcher):
        """datetime.date 对象匹配"""
        from datetime import date

        assert fetcher._match_date(date(2026, 3, 7), "2026-03-07") is True
        assert fetcher._match_date(date(2026, 3, 6), "2026-03-07") is False


class TestNewsFetcherAkshareTransform:
    """NewsFetcherAkshare 数据转换测试"""

    @pytest.fixture
    def fetcher(self):
        return NewsFetcherAkshare()

    def test_transform_cls_news(self, fetcher):
        """财联社新闻转换"""
        df = pd.DataFrame([
            {
                "标题": "测试新闻标题",
                "内容": "测试新闻内容",
                "发布日期": "2026-03-07",
                "发布时间": "10:30:00",
            }
        ])

        # 模拟 _fetch_cls_news 的转换逻辑
        news_items = []
        for _, row in df.iterrows():
            item = NewsItem(
                title=row.get("标题", ""),
                content=row.get("内容", ""),
                date=row.get("发布日期", ""),
                time=row.get("发布时间", ""),
                source="财联社",
            )
            news_items.append(item)

        assert len(news_items) == 1
        assert news_items[0].title == "测试新闻标题"
        assert news_items[0].content == "测试新闻内容"
        assert news_items[0].date == "2026-03-07"
        assert news_items[0].time == "10:30:00"
        assert news_items[0].source == "财联社"

    def test_transform_stock_news(self, fetcher):
        """个股新闻转换"""
        df = pd.DataFrame([
            {
                "新闻标题": "个股测试标题",
                "新闻内容": "个股测试内容",
                "发布时间": "2026-03-07 10:30:00",
                "文章来源": "东方财富",
                "新闻链接": "https://example.com/news/1",
            }
        ])

        # 模拟 _fetch_stock_news 的转换逻辑
        news_items = []
        for _, row in df.iterrows():
            item = NewsItem(
                title=row.get("新闻标题", ""),
                content=row.get("新闻内容", ""),
                date=row.get("发布时间", "")[:10] if row.get("发布时间") else "",
                time=row.get("发布时间", "")[11:19] if row.get("发布时间") else "",
                source=row.get("文章来源", ""),
                url=row.get("新闻链接", ""),
            )
            news_items.append(item)

        assert len(news_items) == 1
        assert news_items[0].title == "个股测试标题"
        assert news_items[0].date == "2026-03-07"
        assert news_items[0].time == "10:30:00"
        assert news_items[0].source == "东方财富"
        assert news_items[0].url == "https://example.com/news/1"


class TestNewsFetcherCls:
    """NewsFetcherCls 入口类测试"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_returns_result(self):
        """fetch 返回正确结果"""

        # Mock 实现
        mock_result = NewsResult(
            news=[NewsItem(title="测试", content="内容", date="2026-03-07")],
            total=1,
            source="财联社_全部",
        )

        # 同时 mock fetch 和 is_available，确保 mock 生效
        with patch(
            "openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher.NewsFetcherAkshare.fetch",
            new_callable=AsyncMock,
            return_value=mock_result,
        ), patch(
            "openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher.NewsFetcherAkshare.is_available",
            return_value=(True, None),
        ):
            fetcher = NewsFetcherCls()
            result = await fetcher.fetch(source="cls_global", limit=10)

            assert result.total == 1
            assert len(result.news) == 1
            assert result.source == "财联社_全部"

    def test_fetcher_name(self):
        """Fetcher 名称"""
        fetcher = NewsFetcherCls()
        assert fetcher.name == "news"


class TestFetchFunction:
    """fetch 便捷函数测试"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_function(self):
        """fetch 函数调用"""
        mock_result = NewsResult(
            news=[NewsItem(title="测试", content="内容", date="2026-03-07")],
            total=1,
            source="test",
        )

        with patch(
            "openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher._fetcher"
        ) as mock_fetcher:
            mock_fetcher.fetch = AsyncMock(return_value=mock_result)

            result = await fetch(source="cls_global", limit=10)

            assert result.total == 1
            mock_fetcher.fetch.assert_called_once_with(
                source="cls_global",
                symbol=None,
                keyword=None,
                date=None,
                limit=10
            )
