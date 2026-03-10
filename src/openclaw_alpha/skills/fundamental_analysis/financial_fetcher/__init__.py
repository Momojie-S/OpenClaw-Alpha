# -*- coding: utf-8 -*-
"""财务指标 Fetcher"""

from .financial_fetcher import FinancialFetcher
from .akshare import FinancialFetcherAkshare
from .tushare import FinancialFetcherTushare

__all__ = ["FinancialFetcher", "FinancialFetcherAkshare", "FinancialFetcherTushare"]

# 注册实现（优先级：Tushare > AKShare）
fetcher = FinancialFetcher()
fetcher.register(FinancialFetcherTushare(), priority=20)
fetcher.register(FinancialFetcherAkshare(), priority=10)


def fetch_financial(code: str):
    """获取财务分析指标

    Args:
        code: 股票代码（如 "000001"）

    Returns:
        财务指标 DataFrame
    """
    return fetcher.fetch(code)
