# -*- coding: utf-8 -*-
"""指数行情获取器"""

import asyncio
from typing import Optional

from openclaw_alpha.data_sources import registry  # noqa: F401

from .index_fetcher import IndexFetcher

# 单例
_fetcher: Optional[IndexFetcher] = None


def _get_fetcher() -> IndexFetcher:
    """获取 IndexFetcher 单例"""
    global _fetcher
    if _fetcher is None:
        _fetcher = IndexFetcher()
    return _fetcher


async def fetch(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[dict]:
    """
    获取指数历史行情数据。

    Args:
        symbol: 指数代码（如 sh000001）
        start_date: 开始日期（YYYYMMDD）
        end_date: 结束日期（YYYYMMDD）

    Returns:
        行情数据列表

    Example:
        >>> data = await fetch("sh000001", "20260301", "20260307")
        >>> print(data[0])
        {
            'date': '2026-03-07',
            'open': 3350.12,
            'high': 3365.45,
            'low': 3340.88,
            'close': 3358.23,
            'volume': 325000000,
            'amount': 4523000000,
        }
    """
    fetcher = _get_fetcher()
    # 将 keyword arguments 转换为 dict 传给基类的 fetch()
    return await fetcher.fetch({
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
    })
