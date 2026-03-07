# -*- coding: utf-8 -*-
"""北向资金数据获取器入口"""

from .akshare_flow import FlowFetcherAkshare


# 全局实例
_fetcher = FlowFetcherAkshare()


async def fetch_daily(date: str | None = None) -> dict:
    """
    获取每日净流入数据

    Args:
        date: 日期 YYYY-MM-DD，默认最近交易日

    Returns:
        每日净流入数据
    """
    return await _fetcher.fetch_daily(date)


async def fetch_stocks(date: str | None = None, direction: str = "inflow") -> list:
    """
    获取个股资金流向

    Args:
        date: 日期 YYYY-MM-DD，默认最近交易日
        direction: 方向 inflow/outflow

    Returns:
        个股资金流向列表
    """
    return await _fetcher.fetch_stocks(date, direction)


async def fetch_trend(days: int = 5, end_date: str | None = None) -> dict:
    """
    获取资金趋势

    Args:
        days: 天数
        end_date: 结束日期，默认最近交易日

    Returns:
        资金趋势数据
    """
    return await _fetcher.fetch_trend(days, end_date)
