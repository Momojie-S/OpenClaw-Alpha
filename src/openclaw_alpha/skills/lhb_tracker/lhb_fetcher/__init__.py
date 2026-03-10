# -*- coding: utf-8 -*-
"""龙虎榜数据获取器"""

from .lhb_fetcher import LhbFetcher, fetch_daily, fetch_stock_history

# 导出旧接口（向后兼容）
from .akshare_lhb import LhbFetcherAkshare

__all__ = [
    "LhbFetcher",
    "LhbFetcherAkshare",  # 向后兼容
    "fetch_daily",
    "fetch_stock_history",
]
