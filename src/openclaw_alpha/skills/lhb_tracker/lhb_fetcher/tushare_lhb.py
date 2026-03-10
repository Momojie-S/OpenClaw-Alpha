# -*- coding: utf-8 -*-
"""Tushare 龙虎榜数据获取实现"""

import asyncio
from datetime import datetime, timedelta
from functools import partial
from typing import Any

from openclaw_alpha.core.fetcher import FetchMethod


class LhbFetcherTushare(FetchMethod):
    """Tushare 龙虎榜数据获取实现

    使用 top_list 接口获取龙虎榜数据。
    积分要求：2000
    """

    name = "lhb_tushare"
    required_data_source = "tushare"
    required_credit = 2000
    priority = 20

    async def fetch(self, date: str | None = None) -> list[dict]:
        """获取每日龙虎榜数据

        Args:
            date: 日期 YYYY-MM-DD，默认最近交易日

        Returns:
            龙虎榜股票列表
        """
        return await self.fetch_daily(date)

    async def fetch_daily(self, date: str | None = None) -> list[dict]:
        """
        获取每日龙虎榜数据

        Args:
            date: 日期 YYYY-MM-DD，默认最近交易日

        Returns:
            龙虎榜股票列表
        """
        # 格式转换：YYYY-MM-DD -> YYYYMMDD
        if date:
            trade_date = date.replace("-", "")
        else:
            # 默认查询最近 3 天，取最新数据
            today = datetime.now()
            # 从今天往前找最近的交易日
            trade_date = await self._find_latest_trade_date(today)

        # 调用 API
        data = await self._call_daily_api(trade_date)

        # 转换数据
        result = self._transform_daily(data)

        return result

    async def fetch_stock_history(
        self, symbol: str, start_date: str | None = None, end_date: str | None = None
    ) -> list[dict]:
        """
        获取个股龙虎榜历史

        通过遍历日期获取龙虎榜数据，然后筛选指定股票。

        Args:
            symbol: 股票代码（6 位数字）
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD

        Returns:
            个股龙虎榜历史
        """
        # 格式转换
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end = datetime.now()

        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            # 默认查询最近 30 天
            start = datetime.now() - timedelta(days=30)

        # Tushare top_list 只支持单日查询，需要遍历日期
        # 这里简化处理：查询最近 30 个交易日
        all_data = []
        current = end
        days_checked = 0
        max_days = 60  # 最多查 60 天（约 40 个交易日）

        while current >= start and days_checked < max_days:
            trade_date = current.strftime("%Y%m%d")
            data = await self._call_daily_api(trade_date)
            if data:
                all_data.extend(data)
            current -= timedelta(days=1)
            days_checked += 1

        # 筛选指定股票
        # ts_code 格式：000001.SZ，需要匹配
        ts_code_pattern = f"{symbol}."
        stock_data = [d for d in all_data if str(d.get("ts_code", "")).startswith(ts_code_pattern)]

        # 转换数据
        result = self._transform_daily(stock_data)

        return result

    async def _find_latest_trade_date(self, from_date: datetime) -> str:
        """查找最近的交易日期

        Args:
            from_date: 起始日期

        Returns:
            交易日期 YYYYMMDD
        """
        # 简化处理：直接返回最近的交易日
        # 如果是周末，返回周五
        weekday = from_date.weekday()
        if weekday == 5:  # 周六
            from_date -= timedelta(days=1)
        elif weekday == 6:  # 周日
            from_date -= timedelta(days=2)

        return from_date.strftime("%Y%m%d")

    async def _call_daily_api(self, trade_date: str) -> list[dict]:
        """调用 Tushare 龙虎榜接口

        Args:
            trade_date: 交易日期 YYYYMMDD

        Returns:
            原始数据列表
        """
        loop = asyncio.get_event_loop()
        try:
            client = await self.get_client()

            # 调用 top_list 接口
            df = await loop.run_in_executor(
                None,
                partial(
                    client.top_list,
                    trade_date=trade_date,
                ),
            )

            if df is None or df.empty:
                return []

            return df.to_dict("records")
        except Exception as e:
            print(f"API 调用失败: {e}")
            return []

    def _transform_daily(self, raw_data: list[dict]) -> list[dict]:
        """
        转换每日龙虎榜数据

        Args:
            raw_data: 原始数据

        Returns:
            转换后的数据（统一格式）
        """
        result = []
        for item in raw_data:
            try:
                # ts_code: 000001.SZ -> 000001
                ts_code = str(item.get("ts_code", ""))
                code = ts_code.split(".")[0] if "." in ts_code else ts_code

                # trade_date: YYYYMMDD -> YYYY-MM-DD
                trade_date = str(item.get("trade_date", ""))
                formatted_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"

                result.append({
                    # 必需字段
                    "code": code,
                    "name": str(item.get("name", "")),
                    "date": formatted_date,
                    "close": self._safe_float(item.get("close", 0)),
                    "change_pct": self._safe_float(item.get("pct_change", 0)),
                    "reason": str(item.get("reason", "")),
                    "buy_amount": self._safe_float(item.get("l_buy", 0)),
                    "sell_amount": self._safe_float(item.get("l_sell", 0)),
                    "net_buy": self._safe_float(item.get("net_amount", 0)),
                    # AKShare 字段（Tushare 没有）
                    "interpretation": None,
                    # Tushare 特有字段
                    "turnover_rate": self._safe_float(item.get("turnover_rate")),
                    "amount": self._safe_float(item.get("amount")),
                    "l_amount": self._safe_float(item.get("l_amount")),
                    "net_rate": self._safe_float(item.get("net_rate")),
                    "amount_rate": self._safe_float(item.get("amount_rate")),
                    "float_values": self._safe_float(item.get("float_values")),
                })
            except Exception as e:
                print(f"转换数据失败: {e}, item: {item}")
                continue

        return result

    def _safe_float(self, value: Any) -> float | None:
        """安全转换为浮点数

        Args:
            value: 原始值

        Returns:
            浮点数或 None
        """
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


# __main__ 入口用于调试
if __name__ == "__main__":
    import json

    async def main():
        fetcher = LhbFetcherTushare()

        print("=== 测试可用性 ===")
        available, error = fetcher.is_available()
        print(f"可用: {available}, 错误: {error}")

        if available:
            print("\n=== 测试每日龙虎榜 ===")
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

            print("\n=== 测试个股龙虎榜历史 ===")
            if daily:
                # 取净买入最多的股票测试
                test_code = sorted_daily[0]["code"]
                history = await fetcher.fetch_stock_history(test_code)
                print(f"股票 {test_code} 上榜次数: {len(history)}")
                if history:
                    print(json.dumps(history[0], ensure_ascii=False, indent=2))

    asyncio.run(main())
