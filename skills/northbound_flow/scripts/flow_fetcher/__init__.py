# -*- coding: utf-8 -*-
"""北向资金数据获取器"""

from .flow_fetcher import fetch_daily, fetch_stocks, fetch_trend
from .akshare_flow import FlowFetcherAkshare

__all__ = ["fetch_daily", "fetch_stocks", "fetch_trend", "FlowFetcherAkshare"]
