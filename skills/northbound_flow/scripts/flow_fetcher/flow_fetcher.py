# -*- coding: utf-8 -*-
"""北向资金数据获取器入口"""

from openclaw_alpha.core.fetcher import Fetcher
from openclaw_alpha.core.registry import DataSourceRegistry
from .tushare_flow import FlowFetcherTushare
from .akshare_flow import FlowFetcherAkshare


class FlowFetcher(Fetcher):
    """北向资金数据获取器

    支持：
    - Tushare：moneyflow_hsgt 接口（优先）
    - AKShare：stock_hsgt_hist_em 接口

    注意：个股资金流向只有 AKShare 支持，Tushare 不支持。
    """

    name = "flow"

    def __init__(self):
        """初始化并注册实现"""
        super().__init__()
        # 注册 Tushare 实现，优先级 20
        self.register(FlowFetcherTushare(), priority=20)
        # 注册 AKShare 实现，优先级 10
        self.register(FlowFetcherAkshare(), priority=10)

    async def fetch_daily(self, date: str | None = None) -> dict:
        """获取每日净流入数据

        优先使用 Tushare，不可用时回退到 AKShare。

        Args:
            date: 日期 YYYY-MM-DD，默认最近交易日

        Returns:
            每日净流入数据
        """
        # 按优先级选择可用的实现
        for method in sorted(self._methods, key=lambda m: m.priority, reverse=True):
            if method.is_available()[0]:
                return await method.fetch_daily(date)
        return None

    async def fetch_trend(self, days: int = 5, end_date: str | None = None) -> dict:
        """获取资金趋势

        优先使用 Tushare，不可用时回退到 AKShare。

        Args:
            days: 天数
            end_date: 结束日期，默认最近交易日

        Returns:
            资金趋势数据
        """
        # 按优先级选择可用的实现
        for method in sorted(self._methods, key=lambda m: m.priority, reverse=True):
            if method.is_available()[0]:
                return await method.fetch_trend(days, end_date)
        return {
            "period": days,
            "total_inflow": 0,
            "avg_inflow": 0,
            "inflow_days": 0,
            "outflow_days": 0,
            "trend": "无数据",
            "daily_data": []
        }

    async def fetch_stocks(self, date: str | None = None, direction: str = "inflow") -> list:
        """获取个股资金流向

        只使用 AKShare，因为 Tushare 不支持个股数据。

        Args:
            date: 日期 YYYY-MM-DD，默认最近交易日
            direction: 方向 inflow/outflow

        Returns:
            个股资金流向列表
        """
        # 个股数据只有 AKShare 支持
        for method in self._methods:
            if method.name == "flow_akshare" and method.is_available()[0]:
                return await method.fetch_stocks(date, direction)
        return []


# 全局实例
_fetcher = None


def _get_fetcher() -> FlowFetcher:
    """获取全局实例（懒加载）"""
    global _fetcher
    if _fetcher is None:
        _fetcher = FlowFetcher()
    return _fetcher


async def fetch_daily(date: str | None = None) -> dict:
    """获取每日净流入数据

    Args:
        date: 日期 YYYY-MM-DD，默认最近交易日

    Returns:
        每日净流入数据
    """
    return await _get_fetcher().fetch_daily(date)


async def fetch_stocks(date: str | None = None, direction: str = "inflow") -> list:
    """获取个股资金流向

    Args:
        date: 日期 YYYY-MM-DD，默认最近交易日
        direction: 方向 inflow/outflow

    Returns:
        个股资金流向列表
    """
    return await _get_fetcher().fetch_stocks(date, direction)


async def fetch_trend(days: int = 5, end_date: str | None = None) -> dict:
    """获取资金趋势

    Args:
        days: 天数
        end_date: 结束日期，默认最近交易日

    Returns:
        资金趋势数据
    """
    return await _get_fetcher().fetch_trend(days, end_date)
