# -*- coding: utf-8 -*-
"""个股数据获取 - Tushare 实现"""

import asyncio
from typing import Any
from datetime import datetime

from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.registry import DataSourceRegistry


class StockFetcherTushare(FetchMethod):
    """个股数据获取 - Tushare 实现

    通过 Tushare 获取股票日线行情数据。
    """

    name = "stock_tushare"
    required_data_source = "tushare"
    priority = 10

    async def fetch(self, params: dict[str, Any]) -> dict[str, Any]:
        """获取个股数据

        Args:
            params: 参数字典，包含：
                - identifier: 股票代码或名称
                - date: 日期（YYYY-MM-DD）

        Returns:
            股票数据字典
        """
        identifier = params.get("identifier")
        date = params.get("date", datetime.now().strftime("%Y-%m-%d"))

        # 1. 解析股票代码（同时获取名称）
        ts_code, stock_name = await self._resolve_code(identifier)

        # 2. 获取日线数据
        daily_data = await self._fetch_daily_data(ts_code, date)

        if not daily_data:
            return {"error": f"未找到 {ts_code} 在 {date} 的数据"}

        # 3. 转换数据格式
        result = self._transform(daily_data, date)
        result["name"] = stock_name
        return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
    )
    async def _resolve_code(self, identifier: str) -> tuple[str, str]:
        """解析股票代码

        Args:
            identifier: 股票代码或名称

        Returns:
            (Tushare 格式的股票代码, 股票名称)
        """
        registry = DataSourceRegistry.get_instance()
        tushare = registry.get("tushare")
        client = await tushare.get_client()

        # 如果是 6 位数字，补充交易所后缀
        if identifier.isdigit() and len(identifier) == 6:
            code = identifier
            # 判断交易所
            if code.startswith(("60", "68")):
                ts_code = f"{code}.SH"
            else:
                ts_code = f"{code}.SZ"

            # 查询股票名称
            df = client.stock_basic(exchange="", list_status="L")
            matched = df[df["ts_code"] == ts_code]
            if len(matched) > 0:
                return ts_code, matched.iloc[0]["name"]
            return ts_code, ""

        # 如果已经是 Tushare 格式
        if "." in identifier:
            df = client.stock_basic(exchange="", list_status="L")
            matched = df[df["ts_code"] == identifier]
            if len(matched) > 0:
                return identifier, matched.iloc[0]["name"]
            return identifier, ""

        # 否则按名称查询
        df = client.stock_basic(exchange="", list_status="L")
        matched = df[df["name"] == identifier]
        if len(matched) > 0:
            return matched.iloc[0]["ts_code"], identifier

        raise ValueError(f"未找到股票：{identifier}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
    )
    async def _fetch_daily_data(self, ts_code: str, date: str) -> dict | None:
        """获取日线数据

        Args:
            ts_code: Tushare 格式的股票代码
            date: 日期（YYYY-MM-DD）

        Returns:
            日线数据字典，或 None
        """
        registry = DataSourceRegistry.get_instance()
        tushare = registry.get("tushare")
        client = await tushare.get_client()

        # 转换日期格式
        trade_date = date.replace("-", "")

        # 获取日线数据
        df = client.daily(ts_code=ts_code, trade_date=trade_date)

        if df.empty:
            # 尝试获取前几天的数据（处理非交易日）
            df = client.daily(
                ts_code=ts_code,
                start_date=trade_date,
                end_date=trade_date,
            )

        if df.empty:
            return None

        return df.iloc[0].to_dict()

    def _transform(self, daily_data: dict, date: str) -> dict[str, Any]:
        """转换数据格式

        Args:
            daily_data: Tushare 返回的日线数据
            date: 日期

        Returns:
            标准格式的股票数据
        """
        ts_code = daily_data.get("ts_code", "")

        return {
            "code": ts_code,
            "name": "",  # 需要额外查询，暂时留空
            "date": date,
            "price": {
                "open": float(daily_data.get("open", 0)),
                "high": float(daily_data.get("high", 0)),
                "low": float(daily_data.get("low", 0)),
                "close": float(daily_data.get("close", 0)),
                "pre_close": float(daily_data.get("pre_close", 0)),
                "change": float(daily_data.get("change", 0)),
                "pct_change": float(daily_data.get("pct_chg", 0)),
            },
            "volume": {
                "volume": float(daily_data.get("vol", 0)) * 100,  # 手 -> 股
                "amount": float(daily_data.get("amount", 0)) * 1000,  # 千元 -> 元
                "turnover_rate": 0.0,  # Tushare daily 接口不提供换手率
            },
            "market_cap": {
                "total": 0.0,  # Tushare daily 接口不提供市值
                "circulation": 0.0,
            },
        }


if __name__ == "__main__":
    # 导入数据源以触发注册
    from openclaw_alpha.data_sources import registry  # noqa: F401

    # 调试入口
    async def main():
        params = {
            "identifier": "000001",
            "date": "2026-03-06",
        }
        fetcher = StockFetcherTushare()
        result = await fetcher.fetch(params)
        print("获取结果：")
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))

    asyncio.run(main())
