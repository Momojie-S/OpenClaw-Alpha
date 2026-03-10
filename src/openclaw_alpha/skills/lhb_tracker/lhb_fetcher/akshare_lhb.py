# -*- coding: utf-8 -*-
"""AKShare 龙虎榜数据获取实现"""

import asyncio
from datetime import datetime, timedelta
from functools import partial
from typing import Any

import akshare as ak

from openclaw_alpha.core.fetcher import FetchMethod


class LhbFetcherAkshare(FetchMethod):
    """AKShare 龙虎榜数据获取实现

    使用 stock_lhb_detail_em 接口获取龙虎榜数据。
    """

    name = "lhb_akshare"
    required_data_source = "akshare"
    priority = 10

    async def fetch(self, date: str | None = None) -> list[dict]:
        """获取每日龙虎榜数据

        注意：AKShare 不支持单独的个股查询，需要通过每日龙虎榜筛选。

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
            start_date = date.replace("-", "")
            end_date = start_date
        else:
            # 默认查询最近 3 天，取最新数据
            today = datetime.now()
            start_date = (today - timedelta(days=3)).strftime("%Y%m%d")
            end_date = today.strftime("%Y%m%d")

        # 调用 API
        data = await self._call_daily_api(start_date, end_date)

        # 转换数据
        result = self._transform_daily(data)

        # 如果指定了日期，只返回该日期的数据
        if date:
            result = [r for r in result if r["date"] == date]

        return result

    async def fetch_stock_history(
        self, symbol: str, start_date: str | None = None, end_date: str | None = None
    ) -> list[dict]:
        """
        获取个股龙虎榜历史

        通过每日龙虎榜接口获取数据，然后筛选指定股票。
        这是因为 stock_lhb_stock_detail_em 需要指定具体日期，不方便查询历史。

        Args:
            symbol: 股票代码（6 位数字）
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD

        Returns:
            个股龙虎榜历史
        """
        # 格式转换
        if end_date:
            end = end_date.replace("-", "")
        else:
            end = datetime.now().strftime("%Y%m%d")

        if start_date:
            start = start_date.replace("-", "")
        else:
            # 默认查询最近 30 天
            start = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

        # 调用每日龙虎榜接口
        data = await self._call_daily_api(start, end)

        # 筛选指定股票
        stock_data = [d for d in data if str(d.get("代码", "")) == symbol]

        # 转换数据（格式与每日龙虎榜一致）
        result = self._transform_daily(stock_data)

        return result

    async def _call_daily_api(self, start_date: str, end_date: str) -> list[dict]:
        """调用 AKShare 每日龙虎榜接口"""
        loop = asyncio.get_event_loop()
        try:
            df = await loop.run_in_executor(
                None, partial(ak.stock_lhb_detail_em, start_date=start_date, end_date=end_date)
            )
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
                # 日期格式：已经是 YYYY-MM-DD 格式
                formatted_date = str(item.get("上榜日", ""))

                # 金额处理（单位：元）
                # 字段名：龙虎榜买入额、龙虎榜卖出额、龙虎榜净买额
                buy_amount = self._safe_float(item.get("龙虎榜买入额", 0))
                sell_amount = self._safe_float(item.get("龙虎榜卖出额", 0))
                net_buy = self._safe_float(item.get("龙虎榜净买额", 0))

                result.append({
                    # 必需字段
                    "code": str(item.get("代码", "")),
                    "name": str(item.get("名称", "")),
                    "date": formatted_date,
                    "close": self._safe_float(item.get("收盘价", 0)),
                    "change_pct": self._safe_float(item.get("涨跌幅", 0)),
                    "reason": str(item.get("上榜原因", "")),
                    "buy_amount": buy_amount,
                    "sell_amount": sell_amount,
                    "net_buy": net_buy,
                    # AKShare 特有字段
                    "interpretation": str(item.get("解读", "")) or None,
                    # Tushare 字段（AKShare 没有）
                    "turnover_rate": None,
                    "amount": None,
                    "l_amount": None,
                    "net_rate": None,
                    "amount_rate": None,
                    "float_values": None,
                })
            except Exception as e:
                print(f"转换数据失败: {e}, item: {item}")
                continue

        return result

    def _safe_float(self, value: Any) -> float:
        """安全转换为浮点数"""
        if value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0


# __main__ 入口用于调试
if __name__ == "__main__":
    import json

    async def main():
        fetcher = LhbFetcherAkshare()

        print("=== 测试可用性 ===")
        available, error = fetcher.is_available()
        print(f"可用: {available}, 错误: {error}")

        if available:
            print("\n=== 测试每日龙虎榜 ===")
            daily = await fetcher.fetch_daily()
            print(f"上榜股票数: {len(daily)}")
            if daily:
                # 按净买入排序
                sorted_daily = sorted(daily, key=lambda x: x["net_buy"], reverse=True)
                print("Top 5 净买入:")
                for stock in sorted_daily[:5]:
                    print(
                        f"  {stock['code']} {stock['name']}: {stock['net_buy']/1e8:.2f}亿 ({stock['reason']})"
                    )
                print("Top 5 净卖出:")
                for stock in sorted_daily[-5:]:
                    print(
                        f"  {stock['code']} {stock['name']}: {stock['net_buy']/1e8:.2f}亿 ({stock['reason']})"
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
