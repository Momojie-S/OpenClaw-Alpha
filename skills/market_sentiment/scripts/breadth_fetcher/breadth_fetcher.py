# -*- coding: utf-8 -*-
"""市场宽度数据获取器

获取创新高/新低的股票数量，用于判断市场趋势的健康程度。
"""

import asyncio
from dataclasses import dataclass
from typing import Optional

import akshare as ak

from openclaw_alpha.core.fetcher import Fetcher, FetchMethod

# 确保数据源已注册
import openclaw_alpha.data_sources  # noqa: F401


@dataclass
class BreadthData:
    """市场宽度数据"""

    date: str
    close: float
    high20: int
    low20: int
    high60: int
    low60: int
    high120: int
    low120: int

    @property
    def breadth_ratio_20(self) -> float:
        """20日宽度比率"""
        total = self.high20 + self.low20
        return self.high20 / total if total > 0 else 0.5

    @property
    def breadth_ratio_60(self) -> float:
        """60日宽度比率"""
        total = self.high60 + self.low60
        return self.high60 / total if total > 0 else 0.5

    @property
    def breadth_ratio_120(self) -> float:
        """120日宽度比率"""
        total = self.high120 + self.low120
        return self.high120 / total if total > 0 else 0.5


class BreadthFetcherAkshare(FetchMethod):
    """AKShare 市场宽度数据获取"""

    name = "breadth_akshare"
    required_data_source = "akshare"
    priority = 1

    async def fetch(self, symbol: str = "all", days: int = 30) -> list[BreadthData]:
        """
        获取市场宽度数据

        Args:
            symbol: 指数类型 (all/sz50/hs300/zz500)
            days: 获取最近几天的数据

        Returns:
            市场宽度数据列表
        """
        # AKShare 接口是同步的，在异步环境中运行
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None, lambda: ak.stock_a_high_low_statistics(symbol=symbol)
        )

        if df.empty:
            return []

        # 按日期降序排列，取最近 days 天
        df = df.sort_values("date", ascending=False).head(days)

        result = []
        for _, row in df.iterrows():
            result.append(
                BreadthData(
                    date=str(row["date"]),
                    close=float(row["close"]),
                    high20=int(row["high20"]),
                    low20=int(row["low20"]),
                    high60=int(row["high60"]),
                    low60=int(row["low60"]),
                    high120=int(row["high120"]),
                    low120=int(row["low120"]),
                )
            )

        return result


class BreadthFetcher(Fetcher):
    """市场宽度数据获取器"""

    name = "breadth"

    def __init__(self):
        super().__init__()
        self.register(BreadthFetcherAkshare())

    async def fetch(
        self, symbol: str = "all", days: int = 30
    ) -> list[BreadthData]:
        """
        获取市场宽度数据

        Args:
            symbol: 指数类型 (all/sz50/hs300/zz500)
            days: 获取最近几天的数据

        Returns:
            市场宽度数据列表
        """
        return await super().fetch(symbol=symbol, days=days)


# 全局实例
_fetcher: Optional[BreadthFetcher] = None


def get_fetcher() -> BreadthFetcher:
    """获取全局 Fetcher 实例"""
    global _fetcher
    if _fetcher is None:
        _fetcher = BreadthFetcher()
    return _fetcher


async def fetch(symbol: str = "all", days: int = 30) -> list[BreadthData]:
    """
    获取市场宽度数据

    Args:
        symbol: 指数类型 (all/sz50/hs300/zz500)
        days: 获取最近几天的数据

    Returns:
        市场宽度数据列表
    """
    return await get_fetcher().fetch(symbol=symbol, days=days)


if __name__ == "__main__":

    async def main():
        data = await fetch(days=10)
        for d in data[:3]:
            print(
                f"{d.date}: 20日新高={d.high20}, 新低={d.low20}, "
                f"宽度比率={d.breadth_ratio_20:.2%}"
            )

    asyncio.run(main())
