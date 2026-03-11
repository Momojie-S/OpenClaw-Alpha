# -*- coding: utf-8 -*-
"""个股实时行情 Fetcher - 入口类"""

from openclaw_alpha.core.fetcher import Fetcher
from openclaw_alpha.skills.stock_screener.stock_spot_fetcher import StockSpot


class StockIndividualSpotFetcher(Fetcher):
    """个股实时行情 Fetcher

    用于获取指定股票列表的实时行情，适用于自选股等场景。
    """

    name = "stock_individual_spot"

    def __init__(self) -> None:
        """初始化 Fetcher"""
        super().__init__()
        # 注册实现（按优先级）
        from .akshare import StockIndividualSpotFetcherAkshare

        self.register(StockIndividualSpotFetcherAkshare(), priority=10)


# 单例实例
_fetcher: StockIndividualSpotFetcher | None = None


def get_fetcher() -> StockIndividualSpotFetcher:
    """获取 Fetcher 单例"""
    global _fetcher
    if _fetcher is None:
        _fetcher = StockIndividualSpotFetcher()
    return _fetcher


async def fetch(codes: list[str]) -> list[StockSpot]:
    """获取指定股票的实时行情

    Args:
        codes: 股票代码列表（6位代码，如 ["000001", "600000"]）

    Returns:
        股票行情列表
    """
    return await get_fetcher().fetch(codes)
