# -*- coding: utf-8 -*-
"""历史行情数据 Fetcher 入口"""

from openclaw_alpha.core.fetcher import Fetcher
from .tushare_impl import HistoryFetcherTushare
from .akshare_impl import HistoryFetcherAkshare


class HistoryFetcher(Fetcher):
    """历史行情数据获取器

    支持：
    - Tushare：pro.daily 接口（优先）
    - AKShare：stock_zh_a_hist 接口
    """

    name = "history"

    def __init__(self):
        """初始化并注册实现"""
        super().__init__()
        # 注册 Tushare 实现，优先级 20
        self.register(HistoryFetcherTushare(), priority=20)
        # 注册 AKShare 实现，优先级 10
        self.register(HistoryFetcherAkshare(), priority=10)


# 全局实例
_fetcher = HistoryFetcher()


async def fetch(symbol: str, start_date: str = None, end_date: str = None, days: int = 60):
    """获取历史行情数据

    Args:
        symbol: 股票代码（如 "000001"）
        start_date: 开始日期（YYYYMMDD）
        end_date: 结束日期（YYYYMMDD）
        days: 天数（默认 60 天）

    Returns:
        DataFrame: 历史行情数据
    """
    return await _fetcher.fetch(symbol=symbol, start_date=start_date, end_date=end_date, days=days)
