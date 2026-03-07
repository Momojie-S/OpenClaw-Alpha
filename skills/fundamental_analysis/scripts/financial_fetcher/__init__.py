# -*- coding: utf-8 -*-
"""财务指标 Fetcher"""

from .financial_fetcher import FinancialFetcher
from .akshare import FinancialFetcherAkshare

__all__ = ["FinancialFetcher", "FinancialFetcherAkshare"]

# 注册默认实现
fetcher = FinancialFetcher()
fetcher.register(FinancialFetcherAkshare(), priority=10)


def fetch_financial(code: str):
    """获取财务分析指标

    Args:
        code: 股票代码（如 "000001"）

    Returns:
        财务指标 DataFrame
    """
    return fetcher.fetch(code)
