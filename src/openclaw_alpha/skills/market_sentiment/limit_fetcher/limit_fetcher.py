# -*- coding: utf-8 -*-
"""涨跌停数据获取器入口"""

from openclaw_alpha.core.fetcher import Fetcher


class LimitFetcher(Fetcher):
    """
    涨跌停数据获取器入口

    调度 Tushare 或 AKShare 实现获取涨跌停统计数据
    """

    name = "limit"

    def __init__(self):
        """初始化，注册实现"""
        super().__init__()

        # 注册实现（优先级：Tushare > AKShare）
        from openclaw_alpha.skills.market_sentiment.limit_fetcher.tushare_impl import LimitFetcherTushare
        from openclaw_alpha.skills.market_sentiment.limit_fetcher.akshare_impl import LimitFetcherAkshare

        self.register(LimitFetcherTushare(), priority=20)
        self.register(LimitFetcherAkshare(), priority=10)


if __name__ == "__main__":
    import asyncio

    async def test():
        fetcher = LimitFetcher()
        result = await fetcher.fetch(date="2026-03-06")
        print(f"涨跌停数据: {result}")

    asyncio.run(test())
