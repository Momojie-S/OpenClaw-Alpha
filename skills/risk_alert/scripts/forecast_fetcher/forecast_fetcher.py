# -*- coding: utf-8 -*-
"""业绩预告 Fetcher 入口"""

from openclaw_alpha.core.fetcher import Fetcher


class ForecastFetcher(Fetcher):
    """业绩预告数据获取器入口"""

    name = "forecast"

    def __init__(self):
        """初始化，注册各个实现"""
        super().__init__()
        # AKShare 实现优先级最高（免费）
        from .akshare import ForecastFetcherAkshare

        self.register(ForecastFetcherAkshare(), priority=10)
