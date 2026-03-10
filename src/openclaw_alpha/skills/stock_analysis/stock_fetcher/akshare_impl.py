# -*- coding: utf-8 -*-
"""个股数据获取 - AKShare 实现"""

import asyncio
from typing import Any
from datetime import datetime, timedelta

from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.registry import DataSourceRegistry


class StockFetcherAkshare(FetchMethod):
    """个股数据获取 - AKShare 实现

    通过 AKShare 获取股票历史行情数据。
    """

    name = "stock_akshare"
    required_data_source = "akshare"
    priority = 5

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

        # 1. 解析股票代码
        code = await self._resolve_code(identifier)

        # 2. 获取历史数据
        hist_data = await self._fetch_hist_data(code, date)

        if hist_data is None or hist_data.empty:
            return {"error": f"未找到 {code} 在 {date} 的数据"}

        # 3. 转换数据格式
        return self._transform(code, hist_data, date)

    async def _resolve_code(self, identifier: str) -> str:
        """解析股票代码

        Args:
            identifier: 股票代码或名称

        Returns:
            6 位股票代码
        """
        # 如果是 6 位数字，直接返回
        if identifier.isdigit() and len(identifier) == 6:
            return identifier

        # 如果是 Tushare 格式，提取代码部分
        if "." in identifier:
            return identifier.split(".")[0]

        # 否则按名称查询
        registry = DataSourceRegistry.get_instance()
        akshare = registry.get("akshare")
        client = await akshare.get_client()

        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        matched = df[df["名称"] == identifier]
        if len(matched) > 0:
            return matched.iloc[0]["代码"]

        raise ValueError(
            f"股票 {identifier} 不存在。"
            f"请检查股票名称是否正确（收到 '{identifier}'）。"
            f"示例：'平安银行'、'贵州茅台'"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
    )
    async def _fetch_hist_data(self, code: str, date: str):
        """获取历史数据

        Args:
            code: 6 位股票代码
            date: 日期（YYYY-MM-DD）

        Returns:
            DataFrame 或 None
        """
        registry = DataSourceRegistry.get_instance()
        akshare = registry.get("akshare")
        client = await akshare.get_client()

        import akshare as ak

        # 计算日期范围（获取一周的数据，确保包含目标日期）
        target_date = datetime.strptime(date, "%Y-%m-%d")
        start_date = (target_date - timedelta(days=7)).strftime("%Y%m%d")
        end_date = target_date.strftime("%Y%m%d")

        try:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",  # 前复权
            )

            if df.empty:
                return None

            # 找到目标日期的数据
            df["日期"] = df["日期"].astype(str)
            target_str = date
            matched = df[df["日期"] == target_str]

            if matched.empty:
                # 返回最近一天的数据
                return df.iloc[-1]

            return matched.iloc[0]

        except Exception as e:
            print(f"AKShare 获取数据失败：{e}")
            return None

    def _transform(self, code: str, daily_data: Any, date: str) -> dict[str, Any]:
        """转换数据格式

        Args:
            code: 股票代码
            daily_data: AKShare 返回的数据
            date: 日期

        Returns:
            标准格式的股票数据
        """
        close = float(daily_data.get("收盘", 0))
        pre_close = float(daily_data.get("收盘", 0)) - float(daily_data.get("涨跌额", 0))
        pct_change = float(daily_data.get("涨跌幅", 0))

        return {
            "code": code,
            "name": str(daily_data.get("股票名称", "")),
            "date": date,
            "price": {
                "open": float(daily_data.get("开盘", 0)),
                "high": float(daily_data.get("最高", 0)),
                "low": float(daily_data.get("最低", 0)),
                "close": close,
                "pre_close": pre_close,
                "change": float(daily_data.get("涨跌额", 0)),
                "pct_change": pct_change,
            },
            "volume": {
                "volume": float(daily_data.get("成交量", 0)),
                "amount": float(daily_data.get("成交额", 0)),
                "turnover_rate": float(daily_data.get("换手率", 0)),
            },
            "market_cap": {
                "total": 0.0,  # AKShare 历史数据不提供市值
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
        fetcher = StockFetcherAkshare()
        result = await fetcher.fetch(params)
        print("获取结果：")
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))

    asyncio.run(main())
