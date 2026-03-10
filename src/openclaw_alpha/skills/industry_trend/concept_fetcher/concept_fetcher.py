# -*- coding: utf-8 -*-
"""概念板块数据获取器"""

from openclaw_alpha.core.fetcher import Fetcher


class ConceptFetcher(Fetcher):
    """概念板块数据获取器

    获取东方财富概念板块数据，包括涨跌幅、换手率、成交额、涨跌家数等。

    注意：Tushare 的 concept 接口只返回代码和名称，没有行情数据，
    因此只使用 AKShare 作为数据源。
    """

    name = "concept"

    def __init__(self):
        """初始化概念板块 Fetcher"""
        super().__init__()

        # 只使用 AKShare（Tushare concept 接口无行情数据）
        from .akshare import ConceptFetcherAkshare

        self.register(ConceptFetcherAkshare(), priority=10)
