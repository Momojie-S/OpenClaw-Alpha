# -*- coding: utf-8 -*-
"""个股数据 Fetcher 入口"""

from openclaw_alpha.core.fetcher import Fetcher
from .tushare_impl import StockFetcherTushare
from .akshare_impl import StockFetcherAkshare


class StockFetcher(Fetcher):
    """个股数据获取器

    支持：
    - Tushare（优先）：日线行情
    - AKShare（备选）：历史行情
    """

    name = "stock"

    def __init__(self):
        """初始化并注册实现"""
        super().__init__()
        # 注册 Tushare 实现，优先级 10
        self.register(StockFetcherTushare(), priority=10)
        # 注册 AKShare 实现，优先级 5
        self.register(StockFetcherAkshare(), priority=5)
