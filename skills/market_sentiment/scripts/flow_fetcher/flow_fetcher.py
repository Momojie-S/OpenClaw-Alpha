# -*- coding: utf-8 -*-
"""资金流向数据获取器入口"""

from openclaw_alpha.core.fetcher import Fetcher


class FlowFetcher(Fetcher):
    """
    资金流向数据获取器入口

    调度 AKShare 实现获取大盘资金流向数据
    """

    name = "flow"

    def __init__(self):
        """初始化，注册实现"""
        super().__init__()

        # 注册 AKShare 实现
        from skills.market_sentiment.scripts.flow_fetcher.akshare_impl import (
            FlowFetcherAkshare,
        )

        self.register(FlowFetcherAkshare(), priority=10)


if __name__ == "__main__":
    import asyncio

    async def test():
        fetcher = FlowFetcher()
        result = await fetcher.fetch(date="2026-03-06")
        print(f"资金流向: {result}")

    asyncio.run(test())
