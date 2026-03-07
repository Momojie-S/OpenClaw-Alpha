# -*- coding: utf-8 -*-
"""龙虎榜数据获取器"""

from .akshare_lhb import LhbFetcherAkshare

# 全局实例
_fetcher = LhbFetcherAkshare()


async def fetch_daily(date: str | None = None) -> list[dict]:
    """
    获取每日龙虎榜数据

    Args:
        date: 日期 YYYY-MM-DD，默认最近交易日

    Returns:
        龙虎榜股票列表
    """
    return await _fetcher.fetch_daily(date)


async def fetch_stock_history(
    symbol: str, start_date: str | None = None, end_date: str | None = None
) -> list[dict]:
    """
    获取个股龙虎榜历史

    Args:
        symbol: 股票代码（6 位数字）
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD

    Returns:
        个股龙虎榜历史
    """
    return await _fetcher.fetch_stock_history(symbol, start_date, end_date)
