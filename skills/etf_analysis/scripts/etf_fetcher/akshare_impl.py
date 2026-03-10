# -*- coding: utf-8 -*-
"""ETF 数据获取 - AKShare 实现"""

import asyncio
from dataclasses import dataclass, asdict
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.registry import DataSourceRegistry


@dataclass
class EtfSpot:
    """ETF 实时行情"""

    code: str
    name: str
    price: float
    change_pct: float
    change: float
    amount: float  # 亿
    volume: float
    open: float
    high: float
    low: float
    prev_close: float


@dataclass
class EtfHistory:
    """ETF 历史数据"""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float


class EtfFetcherAkshare(FetchMethod):
    """ETF 数据获取 - AKShare 实现

    通过 AKShare（新浪财经）获取 ETF 行情数据。
    """

    name = "etf_akshare"
    required_data_source = "akshare"
    priority = 10

    async def fetch(self, params: dict[str, Any]) -> dict[str, Any]:
        """获取 ETF 数据

        Args:
            params: 参数字典，包含：
                - action: 操作类型 (spot/history)
                - symbol: ETF 代码（history 必填）
                - days: 历史天数（history，默认 30）

        Returns:
            ETF 数据字典
        """
        action = params.get("action", "spot")

        if action == "history":
            symbol = params.get("symbol")
            if not symbol:
                return {"error": "history 模式需要指定 symbol"}

            days = params.get("days", 30)
            history = await self._fetch_history(symbol, days)
            return {
                "code": symbol,
                "data": [asdict(h) for h in history],
                "count": len(history),
            }

        # 默认获取实时行情
        spots = await self._fetch_spot()
        return {
            "data": [asdict(s) for s in spots],
            "count": len(spots),
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
    )
    async def _fetch_spot(self) -> list[EtfSpot]:
        """获取全部 ETF 实时行情

        Returns:
            ETF 行情列表
        """
        registry = DataSourceRegistry.get_instance()
        akshare = registry.get("akshare")
        client = await akshare.get_client()

        import akshare as ak
        import pandas as pd

        try:
            df = ak.fund_etf_category_sina(symbol="ETF基金")
        except Exception:
            return []

        result = []
        for _, row in df.iterrows():
            try:
                # 成交额转换为亿
                amount = float(row["成交额"]) / 1e8 if pd.notna(row["成交额"]) else 0
                # 涨跌幅去掉 % 符号
                change_pct = (
                    float(str(row["涨跌幅"]).replace("%", ""))
                    if pd.notna(row["涨跌幅"])
                    else 0
                )

                etf = EtfSpot(
                    code=str(row["代码"]),
                    name=str(row["名称"]),
                    price=float(row["最新价"]) if pd.notna(row["最新价"]) else 0,
                    change_pct=change_pct,
                    change=float(row["涨跌额"]) if pd.notna(row["涨跌额"]) else 0,
                    amount=round(amount, 2),
                    volume=float(row["成交量"]) if pd.notna(row["成交量"]) else 0,
                    open=float(row["今开"]) if pd.notna(row["今开"]) else 0,
                    high=float(row["最高"]) if pd.notna(row["最高"]) else 0,
                    low=float(row["最低"]) if pd.notna(row["最低"]) else 0,
                    prev_close=float(row["昨收"]) if pd.notna(row["昨收"]) else 0,
                )
                result.append(etf)
            except (ValueError, KeyError):
                continue

        return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
    )
    async def _fetch_history(self, symbol: str, days: int = 30) -> list[EtfHistory]:
        """获取 ETF 历史数据

        Args:
            symbol: ETF 代码（如 sz159915）
            days: 历史天数

        Returns:
            历史数据列表
        """
        registry = DataSourceRegistry.get_instance()
        akshare = registry.get("akshare")
        client = await akshare.get_client()

        import akshare as ak
        import pandas as pd

        try:
            df = ak.fund_etf_hist_sina(symbol=symbol)
        except Exception:
            return []

        # 按日期倒序，取最近 days 天
        df = df.sort_values("date", ascending=False).head(days)

        result = []
        for _, row in df.iterrows():
            try:
                hist = EtfHistory(
                    date=str(row["date"]),
                    open=float(row["open"]) if pd.notna(row["open"]) else 0,
                    high=float(row["high"]) if pd.notna(row["high"]) else 0,
                    low=float(row["low"]) if pd.notna(row["low"]) else 0,
                    close=float(row["close"]) if pd.notna(row["close"]) else 0,
                    volume=float(row["volume"]) if pd.notna(row["volume"]) else 0,
                    amount=float(row["amount"]) / 1e8 if pd.notna(row["amount"]) else 0,
                )
                result.append(hist)
            except (ValueError, KeyError):
                continue

        return result


if __name__ == "__main__":
    # 导入数据源以触发注册
    from openclaw_alpha.data_sources import registry  # noqa: F401

    # 调试入口
    async def main():
        fetcher = EtfFetcherAkshare()

        # 测试实时行情
        print("=== 测试实时行情 ===")
        params = {"action": "spot"}
        result = await fetcher.fetch(params)
        print(f"获取 {result['count']} 只 ETF")
        if result["data"]:
            print(f"示例: {result['data'][0]}")

        # 测试历史数据
        print("\n=== 测试历史数据 ===")
        params = {"action": "history", "symbol": "sz159915", "days": 5}
        result = await fetcher.fetch(params)
        print(f"获取 {result['count']} 条历史数据")
        if result["data"]:
            print(f"示例: {result['data'][0]}")

    asyncio.run(main())
