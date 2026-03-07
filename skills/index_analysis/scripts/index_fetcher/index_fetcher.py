# -*- coding: utf-8 -*-
"""指数行情获取器入口"""

from openclaw_alpha.core.fetcher import Fetcher

from .akshare import IndexFetcherAkshare


class IndexFetcher(Fetcher):
    """指数行情获取器入口"""

    name = "index"

    def __init__(self):
        super().__init__()
        # 注册 AKShare 实现
        self.register(IndexFetcherAkshare())
