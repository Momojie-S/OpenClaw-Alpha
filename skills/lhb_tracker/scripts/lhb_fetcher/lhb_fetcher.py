# -*- coding: utf-8 -*-
"""龙虎榜数据获取器入口"""

# 导入数据源模块以注册数据源
import openclaw_alpha.data_sources

from openclaw_alpha.core.fetcher import Fetcher
from .akshare_lhb import LhbFetcherAkshare
from .tushare_lhb import LhbFetcherTushare


class LhbFetcher(Fetcher):
    """龙虎榜数据获取器

    支持：
    - Tushare：top_list 接口（优先，2000积分）
    - AKShare：stock_lhb_detail_em 接口
    """

    name = "lhb"

    def __init__(self):
        """初始化并注册实现"""
        super().__init__()
        # 注册 Tushare 实现，优先级 20
        self.register(LhbFetcherTushare(), priority=20)
        # 注册 AKShare 实现，优先级 10
        self.register(LhbFetcherAkshare(), priority=10)

    async def fetch_daily(self, date: str | None = None) -> list[dict]:
        """获取每日龙虎榜数据

        优先使用 Tushare，不可用时回退到 AKShare。

        Args:
            date: 日期 YYYY-MM-DD，默认最近交易日

        Returns:
            龙虎榜股票列表
        """
        # 按优先级选择可用的实现
        for method in sorted(self._methods, key=lambda m: m.priority, reverse=True):
            available, error = method.is_available()
            if available:
                return await method.fetch_daily(date)

        # 没有可用实现，返回空列表
        return []

    async def fetch_stock_history(
        self, symbol: str, start_date: str | None = None, end_date: str | None = None
    ) -> list[dict]:
        """获取个股龙虎榜历史

        优先使用 Tushare，不可用时回退到 AKShare。

        Args:
            symbol: 股票代码（6 位数字）
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD

        Returns:
            个股龙虎榜历史
        """
        # 按优先级选择可用的实现
        for method in sorted(self._methods, key=lambda m: m.priority, reverse=True):
            available, error = method.is_available()
            if available:
                return await method.fetch_stock_history(symbol, start_date, end_date)

        # 没有可用实现，返回空列表
        return []


# 全局实例
_fetcher = None


def _get_fetcher() -> LhbFetcher:
    """获取全局实例（懒加载）"""
    global _fetcher
    if _fetcher is None:
        _fetcher = LhbFetcher()
    return _fetcher


async def fetch_daily(date: str | None = None) -> list[dict]:
    """获取每日龙虎榜数据

    Args:
        date: 日期 YYYY-MM-DD，默认最近交易日

    Returns:
        龙虎榜股票列表
    """
    return await _get_fetcher().fetch_daily(date)


async def fetch_stock_history(
    symbol: str, start_date: str | None = None, end_date: str | None = None
) -> list[dict]:
    """获取个股龙虎榜历史

    Args:
        symbol: 股票代码（6 位数字）
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD

    Returns:
        个股龙虎榜历史
    """
    return await _get_fetcher().fetch_stock_history(symbol, start_date, end_date)


# __main__ 入口用于调试
if __name__ == "__main__":
    import asyncio
    import json

    async def main():
        fetcher = _get_fetcher()

        print("=== 测试每日龙虎榜 ===")
        daily = await fetcher.fetch_daily()
        print(f"上榜股票数: {len(daily)}")
        if daily:
            # 按净买入排序
            sorted_daily = sorted(daily, key=lambda x: x["net_buy"] or 0, reverse=True)
            print("Top 5 净买入:")
            for stock in sorted_daily[:5]:
                net_buy = stock["net_buy"] or 0
                print(
                    f"  {stock['code']} {stock['name']}: {net_buy/1e8:.2f}亿 ({stock['reason']})"
                )
            print("\n示例数据:")
            print(json.dumps(sorted_daily[0], ensure_ascii=False, indent=2))

        print("\n=== 测试个股龙虎榜历史 ===")
        if daily:
            # 取净买入最多的股票测试
            test_code = sorted_daily[0]["code"]
            history = await fetcher.fetch_stock_history(test_code)
            print(f"股票 {test_code} 上榜次数: {len(history)}")
            if history:
                print(json.dumps(history[0], ensure_ascii=False, indent=2))

    asyncio.run(main())
