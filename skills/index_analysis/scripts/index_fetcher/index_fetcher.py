# -*- coding: utf-8 -*-
"""指数行情获取器入口"""

from openclaw_alpha.core.fetcher import Fetcher


class IndexFetcher(Fetcher):
    """指数行情获取器入口"""

    name = "index"

    def __init__(self):
        super().__init__()
        # 注册实现（优先级：Tushare > AKShare）
        from .tushare import IndexFetcherTushare
        from .akshare import IndexFetcherAkshare

        self.register(IndexFetcherTushare(), priority=20)
        self.register(IndexFetcherAkshare(), priority=10)
