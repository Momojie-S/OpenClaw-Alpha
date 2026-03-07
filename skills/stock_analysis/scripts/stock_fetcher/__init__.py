# -*- coding: utf-8 -*-
"""个股数据获取"""

# 导入数据源以触发注册
from openclaw_alpha.data_sources import registry  # noqa: F401

from .stock_fetcher import StockFetcher

# 全局实例
_fetcher = StockFetcher()


async def fetch(identifier: str, date: str = None) -> dict:
    """获取个股数据

    Args:
        identifier: 股票代码或名称
        date: 日期（YYYY-MM-DD），默认当日

    Returns:
        股票数据字典

    Example:
        >>> data = await fetch("000001", "2026-03-06")
        >>> print(data)
        {
            'code': '000001.SZ',
            'name': '平安银行',
            'date': '2026-03-06',
            'price': {...},
            'volume': {...},
            'market_cap': {...}
        }
    """
    from datetime import datetime

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    params = {
        "identifier": identifier,
        "date": date,
    }

    return await _fetcher.fetch(params)
