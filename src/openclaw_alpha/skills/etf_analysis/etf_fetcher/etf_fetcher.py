# -*- coding: utf-8 -*-
"""ETF 数据 Fetcher 入口"""

from openclaw_alpha.core.fetcher import Fetcher
from .akshare_impl import EtfFetcherAkshare
from .tushare_impl import EtfFetcherTushare


class EtfFetcher(Fetcher):
    """ETF 数据获取器

    支持：
    - Tushare：历史数据（5000积分）
    - AKShare（新浪财经）：实时行情 + 历史数据
    """

    name = "etf"

    def __init__(self):
        """初始化并注册实现"""
        super().__init__()
        # 注册实现（优先级：Tushare > AKShare）
        self.register(EtfFetcherTushare(), priority=20)
        self.register(EtfFetcherAkshare(), priority=10)
