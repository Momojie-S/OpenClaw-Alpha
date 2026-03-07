# -*- coding: utf-8 -*-
"""AKShare 北向资金数据获取实现"""

import akshare as ak
import asyncio
from datetime import datetime, timedelta
from functools import partial
from typing import Any


class FlowFetcherAkshare:
    """AKShare 北向资金数据获取实现

    注意：北向资金只有 AKShare 一个免费数据源，不需要多数据源调度，
    因此不继承 FetchMethod，简化设计。
    """

    name = "flow_akshare"

    async def fetch_daily(self, date: str | None = None) -> dict:
        """
        获取每日净流入数据

        Args:
            date: 日期 YYYY-MM-DD，默认最近交易日

        Returns:
            每日净流入数据
        """
        # 并行获取沪股通和深股通数据
        sh_data, sz_data = await asyncio.gather(
            self._call_hist_api("沪股通"),
            self._call_hist_api("深股通")
        )

        # 转换数据
        sh_flows = self._transform_hist(sh_data)
        sz_flows = self._transform_hist(sz_data)

        # 合并数据
        combined = self._combine_flows(sh_flows, sz_flows)

        # 筛选指定日期
        if date:
            combined = [d for d in combined if d["date"] == date]
            if not combined:
                return None
            return combined[0]

        # 返回最近交易日
        if combined:
            return combined[0]

        return None

    async def fetch_stocks(self, date: str | None = None, direction: str = "inflow") -> list:
        """
        获取个股资金流向

        Args:
            date: 日期 YYYY-MM-DD，默认最近交易日
            direction: 方向 inflow/outflow

        Returns:
            个股资金流向列表
        """
        data = await self._call_stocks_api()

        # 转换数据
        stocks = self._transform_stocks(data)

        # 筛选指定日期（如果有的话）
        # 注意：个股数据可能没有日期字段或日期不一致

        # 按持仓变化排序
        if direction == "inflow":
            # 按持仓变化降序（正值）
            stocks = sorted(stocks, key=lambda x: x["hold_change"], reverse=True)
            stocks = [s for s in stocks if s["hold_change"] > 0]
        else:
            # 按持仓变化升序（负值）
            stocks = sorted(stocks, key=lambda x: x["hold_change"])
            stocks = [s for s in stocks if s["hold_change"] < 0]

        return stocks

    async def fetch_trend(self, days: int = 5, end_date: str | None = None) -> dict:
        """
        获取资金趋势

        Args:
            days: 天数
            end_date: 结束日期，默认最近交易日

        Returns:
            资金趋势数据
        """
        # 并行获取沪股通和深股通数据
        sh_data, sz_data = await asyncio.gather(
            self._call_hist_api("沪股通"),
            self._call_hist_api("深股通")
        )

        # 转换数据
        sh_flows = self._transform_hist(sh_data)
        sz_flows = self._transform_hist(sz_data)

        # 合并数据
        combined = self._combine_flows(sh_flows, sz_flows)

        # 按日期排序（升序）
        combined.sort(key=lambda x: x["date"])

        # 筛选日期范围
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = datetime.now()

        # 获取近 N 个交易日
        filtered_data = []
        for d in reversed(combined):
            dt = datetime.strptime(d["date"], "%Y-%m-%d")
            if dt <= end_dt:
                filtered_data.append(d)
                if len(filtered_data) >= days:
                    break

        filtered_data.reverse()  # 恢复时间顺序

        if not filtered_data:
            return {
                "period": days,
                "total_inflow": 0,
                "avg_inflow": 0,
                "inflow_days": 0,
                "outflow_days": 0,
                "trend": "无数据",
                "daily_data": []
            }

        # 计算趋势
        total_inflow = sum(d["total_flow"] for d in filtered_data)
        avg_inflow = total_inflow / len(filtered_data)
        inflow_days = sum(1 for d in filtered_data if d["total_flow"] > 0)
        outflow_days = sum(1 for d in filtered_data if d["total_flow"] < 0)

        # 判断趋势
        if inflow_days >= days * 0.7:
            trend = "持续流入"
        elif outflow_days >= days * 0.7:
            trend = "持续流出"
        else:
            trend = "震荡"

        return {
            "period": days,
            "total_inflow": round(total_inflow, 2),
            "avg_inflow": round(avg_inflow, 2),
            "inflow_days": inflow_days,
            "outflow_days": outflow_days,
            "trend": trend,
            "daily_data": filtered_data
        }

    async def _call_hist_api(self, symbol: str) -> list[dict]:
        """调用 AKShare 历史资金流向接口"""
        # AKShare 接口是同步的，需要在异步环境中运行
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None,
            partial(ak.stock_hsgt_hist_em, symbol)
        )

        return df.to_dict("records")

    async def _call_stocks_api(self) -> list[dict]:
        """调用 AKShare 个股持股接口"""
        # AKShare 接口是同步的，需要在异步环境中运行
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None,
            partial(ak.stock_hsgt_hold_stock_em, "北向")
        )

        return df.to_dict("records")

    def _transform_hist(self, raw_data: list[dict]) -> list[dict]:
        """
        转换历史资金流向数据

        Args:
            raw_data: 原始数据

        Returns:
            转换后的数据
        """
        result = []
        for item in raw_data:
            # 日期格式：YYYY-MM-DD
            date = str(item.get("日期", ""))

            # 当日成交净买额（亿元）
            # 注意：原始数据单位是亿元，可能有 NaN
            net_buy_raw = item.get("当日成交净买额", 0)

            # 跳过 NaN 数据
            if net_buy_raw is None or str(net_buy_raw) == "nan":
                continue

            try:
                net_buy = float(net_buy_raw)
            except (ValueError, TypeError):
                continue

            result.append({
                "date": date,
                "net_buy": round(net_buy, 2)
            })

        return result

    def _combine_flows(self, sh_flows: list[dict], sz_flows: list[dict]) -> list[dict]:
        """
        合并沪股通和深股通数据

        Args:
            sh_flows: 沪股通数据
            sz_flows: 深股通数据

        Returns:
            合并后的数据
        """
        # 创建日期索引
        sh_dict = {d["date"]: d["net_buy"] for d in sh_flows}
        sz_dict = {d["date"]: d["net_buy"] for d in sz_flows}

        # 获取所有日期
        all_dates = set(sh_dict.keys()) | set(sz_dict.keys())

        # 合并数据
        result = []
        for date in sorted(all_dates, reverse=True):
            sh_flow = sh_dict.get(date, 0)
            sz_flow = sz_dict.get(date, 0)
            total_flow = sh_flow + sz_flow

            # 状态判断
            status = self._get_status(total_flow)

            result.append({
                "date": date,
                "sh_flow": round(sh_flow, 2),
                "sz_flow": round(sz_flow, 2),
                "total_flow": round(total_flow, 2),
                "status": status
            })

        return result

    def _transform_stocks(self, raw_data: list[dict]) -> list[dict]:
        """
        转换个股资金流向数据

        Args:
            raw_data: 原始数据

        Returns:
            转换后的数据
        """
        result = []
        for item in raw_data:
            # 5日增持估计-市值（万元）
            # 注意：这是5日的变化，不是单日
            hold_change = float(item.get("5日增持估计-市值", 0) or 0)
            hold_ratio = float(item.get("5日增持估计-占流通股比", 0) or 0)

            result.append({
                "code": str(item.get("代码", "")),
                "name": str(item.get("名称", "")),
                "hold_change": round(hold_change, 2),
                "hold_ratio": round(hold_ratio, 4),
                "direction": "流入" if hold_change > 0 else "流出",
                "date": str(item.get("日期", ""))
            })

        return result

    def _get_status(self, total_flow: float) -> str:
        """
        判断资金状态

        Args:
            total_flow: 净流入金额（亿元）

        Returns:
            状态
        """
        if total_flow > 50:
            return "大幅流入"
        elif total_flow > 10:
            return "流入"
        elif total_flow >= -10:
            return "平衡"
        elif total_flow >= -50:
            return "流出"
        else:
            return "大幅流出"


# __main__ 入口用于调试
if __name__ == "__main__":
    import asyncio
    import json

    async def main():
        fetcher = FlowFetcherAkshare()

        print("=== 测试每日净流入 ===")
        daily = await fetcher.fetch_daily()
        print(json.dumps(daily, ensure_ascii=False, indent=2))

        print("\n=== 测试个股流入 ===")
        stocks_in = await fetcher.fetch_stocks(direction="inflow")
        print(f"流入股票数: {len(stocks_in)}")
        if stocks_in:
            print(json.dumps(stocks_in[:5], ensure_ascii=False, indent=2))

        print("\n=== 测试个股流出 ===")
        stocks_out = await fetcher.fetch_stocks(direction="outflow")
        print(f"流出股票数: {len(stocks_out)}")
        if stocks_out:
            print(json.dumps(stocks_out[:5], ensure_ascii=False, indent=2))

        print("\n=== 测试资金趋势 ===")
        trend = await fetcher.fetch_trend(days=5)
        print(json.dumps({
            "period": trend["period"],
            "total_inflow": trend["total_inflow"],
            "avg_inflow": trend["avg_inflow"],
            "inflow_days": trend["inflow_days"],
            "outflow_days": trend["outflow_days"],
            "trend": trend["trend"]
        }, ensure_ascii=False, indent=2))

    asyncio.run(main())
