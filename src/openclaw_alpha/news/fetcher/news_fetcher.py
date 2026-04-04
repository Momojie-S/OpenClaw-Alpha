# -*- coding: utf-8 -*-
"""新闻数据 Fetcher 主入口"""

import asyncio
from typing import Optional

from openclaw_alpha.core.fetcher import Fetcher
from .models import NewsItem, NewsResult
from .akshare_impl import NewsFetcherAkshare
from .rsshub_impl import NewsFetcherRsshub


class NewsFetcherCls(Fetcher):
    """新闻数据 Fetcher 入口类"""

    name = "news"

    def __init__(self):
        super().__init__()
        self.register(NewsFetcherAkshare(), priority=10)
        self.register(NewsFetcherRsshub(), priority=5)

    async def fetch(
        self,
        source: str = "cls_global",
        symbol: Optional[str] = None,
        keyword: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 20
    ) -> NewsResult:
        sorted_methods = sorted(self._methods, key=lambda m: m.priority, reverse=True)

        last_error = None
        for method in sorted_methods:
            available, error = method.is_available()
            if not available:
                last_error = error
                continue

            try:
                result = await method.fetch(
                    source=source,
                    symbol=symbol,
                    keyword=keyword,
                    date=date,
                    limit=limit
                )
                if result.total > 0:
                    return result
                if result.source.endswith("_unsupported"):
                    continue
                return result
            except Exception as e:
                last_error = e
                continue

        if last_error:
            raise last_error
        return NewsResult(news=[], total=0, source="")


# 单例
_fetcher = None


def _get_fetcher():
    global _fetcher
    if _fetcher is None:
        _fetcher = NewsFetcherCls()
    return _fetcher


async def fetch(
    source: str = "cls_global",
    symbol: Optional[str] = None,
    keyword: Optional[str] = None,
    date: Optional[str] = None,
    limit: int = 20
) -> NewsResult:
    """获取新闻数据"""
    return await _get_fetcher().fetch(
        source=source,
        symbol=symbol,
        keyword=keyword,
        date=date,
        limit=limit
    )


def _main():
    """命令行入口"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="获取财经新闻")
    parser.add_argument(
        "--source",
        default="cls_global",
        help="新闻源"
    )
    parser.add_argument("--symbol", help="股票代码")
    parser.add_argument("--keyword", help="关键词筛选")
    parser.add_argument("--date", help="日期筛选（YYYY-MM-DD）")
    parser.add_argument("--limit", type=int, default=20, help="返回数量限制")

    args = parser.parse_args()

    result = asyncio.run(fetch(
        source=args.source,
        symbol=args.symbol,
        keyword=args.keyword,
        date=args.date,
        limit=args.limit
    ))

    output = {
        "source": result.source,
        "total": result.total,
        "news": [
            {
                "news_id": item.news_id,
                "title": item.title,
                "content": item.content[:200] + "..." if len(item.content) > 200 else item.content,
                "date": str(item.date) if item.date else "",
                "time": str(item.time) if item.time else "",
                "source": item.source,
            }
            for item in result.news
        ]
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _main()
