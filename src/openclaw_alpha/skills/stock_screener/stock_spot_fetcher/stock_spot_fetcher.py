# -*- coding: utf-8 -*-
"""全市场股票行情 Fetcher - 入口类"""

from dataclasses import dataclass

from openclaw_alpha.core.fetcher import Fetcher


@dataclass
class StockSpot:
    """股票行情数据"""

    code: str  # 代码
    name: str  # 名称
    change_pct: float  # 涨跌幅（%）
    turnover_rate: float  # 换手率（%）
    amount: float  # 成交额（亿元）
    price: float  # 最新价（元）
    market_cap: float  # 总市值（亿元）


class StockSpotFetcher(Fetcher):
    """全市场股票行情 Fetcher"""

    name = "stock_spot"

    async def fetch(self) -> list[StockSpot]:
        """
        获取全市场股票行情

        Returns:
            股票行情列表
        """
        method = self._select_available()
        return await method.fetch()


# 单例实例
_fetcher: StockSpotFetcher | None = None


def get_fetcher() -> StockSpotFetcher:
    """获取 Fetcher 单例"""
    global _fetcher
    if _fetcher is None:
        _fetcher = StockSpotFetcher()
    return _fetcher


async def fetch() -> list[StockSpot]:
    """获取全市场股票行情（便捷函数）"""
    return await get_fetcher().fetch()
