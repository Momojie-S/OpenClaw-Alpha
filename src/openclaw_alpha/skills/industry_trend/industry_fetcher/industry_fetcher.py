# -*- coding: utf-8 -*-
"""行业板块 Fetcher 入口"""

from openclaw_alpha.core.fetcher import Fetcher
from .tushare import IndustryFetcherTushare


class IndustryFetcher(Fetcher):
    """行业板块数据获取器

    支持：
    - Tushare（优先）：申万行业分类 + 日线数据
    """

    name = "industry"

    def __init__(self):
        """初始化并注册实现"""
        super().__init__()
        # 注册 Tushare 实现，优先级 10
        self.register(IndustryFetcherTushare(), priority=10)
