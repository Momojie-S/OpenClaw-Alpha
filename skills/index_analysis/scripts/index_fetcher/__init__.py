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
    """
    fetcher = _get_fetcher()
    return await fetcher.fetch(symbol, start_date, end_date)
