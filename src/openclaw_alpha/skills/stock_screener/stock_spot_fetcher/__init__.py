# -*- coding: utf-8 -*-
"""全市场股票行情 Fetcher"""

from .stock_spot_fetcher import StockSpotFetcher, StockSpot, fetch

# 导入实现模块以触发自动注册
from . import akshare

__all__ = ["StockSpotFetcher", "StockSpot", "fetch"]
