# -*- coding: utf-8 -*-
"""全市场股票行情 Fetcher - AKShare 实现"""

import asyncio
import logging

import akshare as ak
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.exceptions import NetworkError, RateLimitError, ServerError
from openclaw_alpha.core.fetcher import FetchMethod
from .stock_spot_fetcher import StockSpot, StockSpotFetcher

logger = logging.getLogger(__name__)


class StockSpotFetcherAkshare(FetchMethod):
    """AKShare 实现"""

    name = "stock_spot_akshare"
    required_data_source = "akshare"
    priority = 10

    def __init__(self):
        """初始化"""
        super().__init__()
        # 注册到 Fetcher 单例
        from .stock_spot_fetcher import get_fetcher
        fetcher = get_fetcher()
        fetcher.register(self, self.priority)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    async def _call_api(self) -> pd.DataFrame:
        """
        调用 AKShare API 获取全市场行情

        Returns:
            原始 DataFrame

        Raises:
            NetworkError: 网络错误
            RateLimitError: 限流
            ServerError: 服务端错误
        """
        try:
            # stock_zh_a_spot_em 返回所有 A 股实时行情
            df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
            return df
        except Exception as e:
            error_msg = str(e).lower()
            if "rate" in error_msg or "limit" in error_msg or "429" in error_msg:
                raise RateLimitError(f"AKShare 限流: {e}")
            elif "timeout" in error_msg or "connection" in error_msg:
                raise NetworkError(f"网络错误: {e}")
            elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                raise ServerError(f"服务端错误: {e}")
            else:
                raise

    def _transform(self, df: pd.DataFrame) -> list[StockSpot]:
        """
        转换原始数据为 StockSpot 列表

        Args:
            df: 原始 DataFrame

        Returns:
            StockSpot 列表
        """
        if df is None or df.empty:
            return []

        spots = []
        for _, row in df.iterrows():
            try:
                # 跳过停牌或无数据的股票
                if pd.isna(row.get("涨跌幅")) or pd.isna(row.get("最新价")):
                    continue

                # 单位转换
                # 成交额：元 -> 亿元
                amount = row.get("成交额", 0)
                if pd.notna(amount) and amount > 0:
                    amount = amount / 1e8
                else:
                    amount = 0.0

                # 市值：元 -> 亿元
                market_cap = row.get("总市值", 0)
                if pd.notna(market_cap) and market_cap > 0:
                    market_cap = market_cap / 1e8
                else:
                    market_cap = 0.0

                spot = StockSpot(
                    code=str(row.get("代码", "")),
                    name=str(row.get("名称", "")),
                    change_pct=float(row.get("涨跌幅", 0) or 0),
                    turnover_rate=float(row.get("换手率", 0) or 0),
                    amount=round(amount, 2),
                    price=float(row.get("最新价", 0) or 0),
                    market_cap=round(market_cap, 2),
                )
                spots.append(spot)
            except Exception as e:
                logger.warning(f"转换股票数据失败: {row.get('代码', 'unknown')}, {e}")
                continue

        return spots

    async def fetch(self) -> list[StockSpot]:
        """
        获取全市场股票行情

        Returns:
            StockSpot 列表
        """
        df = await self._call_api()
        return self._transform(df)


# 自动注册
_instance = StockSpotFetcherAkshare()


# 调试入口
if __name__ == "__main__":
    import asyncio

    async def test():
        fetcher = StockSpotFetcherAkshare()
        print("正在获取全市场行情...")
        spots = await fetcher.fetch()
        print(f"获取到 {len(spots)} 只股票")
        if spots:
            print("\n前 5 只股票：")
            for spot in spots[:5]:
                print(f"  {spot.code} {spot.name}: 涨幅 {spot.change_pct}%, 换手 {spot.turnover_rate}%, 市值 {spot.market_cap} 亿")

    asyncio.run(test())
