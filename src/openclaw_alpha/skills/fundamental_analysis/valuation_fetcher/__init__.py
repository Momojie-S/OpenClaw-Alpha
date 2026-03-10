# -*- coding: utf-8 -*-
"""估值数据 Fetcher"""

from .valuation_fetcher import ValuationFetcher
from .akshare import ValuationFetcherAkshare
from .tushare import ValuationFetcherTushare

__all__ = ["ValuationFetcher", "ValuationFetcherAkshare", "ValuationFetcherTushare"]

# 注册实现（优先级：Tushare > AKShare）
fetcher = ValuationFetcher()
fetcher.register(ValuationFetcherTushare(), priority=20)
fetcher.register(ValuationFetcherAkshare(), priority=10)


def fetch_valuation(code: str, indicator: str, period: str = "近一年"):
    """获取估值数据

    Args:
        code: 股票代码（如 "000001"）
        indicator: 指标类型（"pe_ttm", "pe_static", "pb", "market_cap", "pcf"）
        period: 时间范围（默认 "近一年"）

    Returns:
        估值时间序列数据列表
    """
    return fetcher.fetch(code, indicator, period)
