# -*- coding: utf-8 -*-
"""北向资金数据获取器"""

# 导入数据源以触发注册
from openclaw_alpha.data_sources import registry  # noqa: F401

from .flow_fetcher import fetch_daily, fetch_stocks, fetch_trend
from .akshare_flow import FlowFetcherAkshare
from .tushare_flow import FlowFetcherTushare

__all__ = [
    "fetch_daily",
    "fetch_stocks",
    "fetch_trend",
    "FlowFetcherAkshare",
    "FlowFetcherTushare",
]
