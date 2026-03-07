# -*- coding: utf-8 -*-
"""概念板块数据获取器"""

from openclaw_alpha.core.fetcher import Fetcher
from .akshare import ConceptFetcherAkshare


class ConceptFetcher(Fetcher):
    """概念板块数据获取器
    
    获取东方财富概念板块数据，包括涨跌幅、换手率、成交额、涨跌家数等。
    """
    
    name = "concept"
    
    def __init__(self):
        """初始化概念板块 Fetcher"""
        super().__init__()
        
        # 注册 AKShare 实现（唯一实现）
        self.register(ConceptFetcherAkshare(), priority=10)
