# -*- coding: utf-8 -*-
"""AKShare 新闻数据获取实现"""

import asyncio
import hashlib
from typing import Optional

import akshare as ak

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.data_sources import registry  # noqa: F401
from .models import NewsItem, NewsResult


class NewsFetcherAkshare(FetchMethod):
    """AKShare 新闻数据获取实现"""

    name = "news_akshare"
    required_data_source = "akshare"
    priority = 10

    SUPPORTED_SOURCES = {"cls_global", "cls_important", "stock"}

    async def fetch(
        self,
        source: str = "cls_global",
        symbol: Optional[str] = None,
        keyword: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 20
    ) -> NewsResult:
        if source not in self.SUPPORTED_SOURCES:
            return NewsResult(news=[], total=0, source="akshare_unsupported")

        fetch_limit = limit * 5 if keyword or date else limit

        if source == "cls_global":
            result = await self._fetch_cls_news(symbol="全部", limit=fetch_limit)
        elif source == "cls_important":
            result = await self._fetch_cls_news(symbol="重点", limit=fetch_limit)
        elif source == "stock":
            if not symbol:
                raise ValueError(
                    "参数 symbol 缺失（必填）。"
                    "个股新闻必须指定股票代码，例如：--symbol 000001"
                )
            result = await self._fetch_stock_news(symbol=symbol, limit=fetch_limit)
        else:
            result = NewsResult(news=[], total=0, source="")

        filtered_news = self._filter_news(result.news, keyword=keyword, date=date)
        filtered_news = filtered_news[:limit]

        return NewsResult(
            news=filtered_news,
            total=len(filtered_news),
            source=result.source
        )

    @staticmethod
    def generate_news_id(source: str, title: str, date: str, time: str = "") -> str:
        """生成 AKShare 源的 news_id"""
        raw = f"{title}{date}{time}"
        hash_str = hashlib.md5(raw.encode()).hexdigest()[:12]
        return f"{source}_{hash_str}"

    def _filter_news(
        self,
        news: list[NewsItem],
        keyword: Optional[str] = None,
        date: Optional[str] = None
    ) -> list[NewsItem]:
        result = news
        if keyword:
            keyword_lower = keyword.lower()
            result = [
                item for item in result
                if keyword_lower in item.title.lower()
                or keyword_lower in item.content.lower()
            ]
        if date:
            result = [
                item for item in result
                if self._match_date(item.date, date)
            ]
        return result

    @staticmethod
    def _match_date(item_date, target_date: str) -> bool:
        date_str = item_date if isinstance(item_date, str) else str(item_date)
        return date_str == target_date or date_str.startswith(target_date)

    async def _fetch_cls_news(self, symbol: str = "全部", limit: int = 20) -> NewsResult:
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None,
            lambda: ak.stock_info_global_cls(symbol=symbol)
        )
        if len(df) > limit:
            df = df.head(limit)

        news_items = []
        for _, row in df.iterrows():
            title = row.get("标题", "")
            date_str = str(row.get("发布日期", ""))
            time_str = str(row.get("发布时间", ""))
            news_items.append(NewsItem(
                news_id=self.generate_news_id("cls_global", title, date_str, time_str),
                title=title,
                content=row.get("内容", ""),
                date=date_str,
                time=time_str,
                source="财联社",
            ))

        return NewsResult(
            news=news_items,
            total=len(news_items),
            source=f"财联社_{symbol}"
        )

    async def _fetch_stock_news(self, symbol: str, limit: int = 20) -> NewsResult:
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None,
            lambda: ak.stock_news_em(symbol=symbol)
        )
        if len(df) > limit:
            df = df.head(limit)

        news_items = []
        for _, row in df.iterrows():
            pub_time = str(row.get("发布时间", ""))
            title = row.get("新闻标题", "")
            news_items.append(NewsItem(
                news_id=self.generate_news_id("stock", title, pub_time[:10], pub_time[11:19]),
                title=title,
                content=row.get("新闻内容", ""),
                date=pub_time[:10] if pub_time else "",
                time=pub_time[11:19] if pub_time else "",
                source=row.get("文章来源", ""),
                url=row.get("新闻链接", ""),
            ))

        return NewsResult(
            news=news_items,
            total=len(news_items),
            source=f"东方财富_{symbol}"
        )
