# -*- coding: utf-8 -*-
"""Tushare 北向资金数据获取实现"""

import asyncio
from datetime import datetime
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.registry import DataSourceRegistry


class FlowFetcherTushare(FetchMethod):
    """Tushare 北向资金数据获取实现

    通过 Tushare moneyflow_hsgt 接口获取北向资金数据。

    注意：Tushare 不支持个股资金流向，个股数据仍需 AKShare。
    """

    name = "flow_tushare"
    required_data_source = "tushare"
    required_credit = 0  # moneyflow_hsgt 基础积分即可
    priority = 20  # 优先级高于 AKShare

    async def fetch(self, params: dict[str, Any]) -> Any:
        """通用 fetch 方法（基类要求）

        Args:
            params: 参数字典，包含：
                - method: 要调用的方法名（fetch_daily/fetch_trend/fetch_stocks）
                - 其他方法参数

        Returns:
            方法执行结果
        """
        method = params.get("method", "fetch_daily")
        if method == "fetch_daily":
            return await self.fetch_daily(params.get("date"))
        elif method == "fetch_trend":
            return await self.fetch_trend(params.get("days", 5), params.get("end_date"))
        elif method == "fetch_stocks":
            # Tushare 不支持个股，返回空列表
            return []
        else:
            raise ValueError(
                f"参数 method '{method}' 不存在（收到 '{method}'）。"
                f"可用方法：fetch_daily（每日净流入）、fetch_trend（趋势分析）、fetch_stocks（个股流向）"
            )

    async def fetch_daily(self, date: str | None = None) -> dict:
        """
        获取每日净流入数据

        Args:
            date: 日期 YYYY-MM-DD，默认最近交易日

        Returns:
            每日净流入数据
        """
        # 获取数据
        data = await self._call_api(date)

        if not data:
            return None

        # 转换数据
        result = self._transform_daily(data)

        # 筛选指定日期
        if date:
            for d in result:
                if d["date"] == date:
                    return d
            return None

        # 返回最近交易日
        if result:
            return result[0]

        return None

    async def fetch_trend(self, days: int = 5, end_date: str | None = None) -> dict:
        """
        获取资金趋势

        Args:
            days: 天数
            end_date: 结束日期，默认最近交易日

        Returns:
            资金趋势数据
        """
        # 计算日期范围（多获取一些天数确保有足够交易日）
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = datetime.now()

        # Tushare 日期格式：YYYYMMDD
        end_date_ts = end_dt.strftime("%Y%m%d")

        # 获取数据
        data = await self._call_api_range(end_date=end_date_ts, days=days * 2)

        if not data:
            return {
                "period": days,
                "total_inflow": 0,
                "avg_inflow": 0,
                "inflow_days": 0,
                "outflow_days": 0,
                "trend": "无数据",
                "daily_data": []
            }

        # 转换数据
        result = self._transform_daily(data)

        # 按日期排序（升序）
        result.sort(key=lambda x: x["date"])

        # 筛选日期范围
        filtered_data = []
        for d in reversed(result):
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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
    )
    async def _call_api(self, date: str | None = None) -> list[dict]:
        """
        调用 Tushare moneyflow_hsgt 接口

        Args:
            date: 日期 YYYY-MM-DD

        Returns:
            原始数据列表
        """
        registry = DataSourceRegistry.get_instance()
        tushare = registry.get("tushare")
        client = await tushare.get_client()

        # Tushare moneyflow_hsgt 必须提供日期参数
        # 如果没有指定日期，获取最近 10 天的数据
        if date:
            trade_date = date.replace("-", "")
            df = client.moneyflow_hsgt(trade_date=trade_date)
        else:
            # 获取最近 10 天的数据
            from datetime import timedelta
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")
            df = client.moneyflow_hsgt(start_date=start_date, end_date=end_date)

        if df.empty:
            return []

        return df.to_dict("records")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
    )
    async def _call_api_range(self, end_date: str, days: int = 30) -> list[dict]:
        """
        调用 Tushare moneyflow_hsgt 接口获取日期范围数据

        Args:
            end_date: 结束日期 YYYYMMDD
            days: 天数

        Returns:
            原始数据列表
        """
        registry = DataSourceRegistry.get_instance()
        tushare = registry.get("tushare")
        client = await tushare.get_client()

        # 计算开始日期
        from datetime import timedelta
        end_dt = datetime.strptime(end_date, "%Y%m%d")
        start_dt = end_dt - timedelta(days=days)
        start_date = start_dt.strftime("%Y%m%d")

        df = client.moneyflow_hsgt(start_date=start_date, end_date=end_date)

        if df.empty:
            return []

        return df.to_dict("records")

    def _transform_daily(self, raw_data: list[dict]) -> list[dict]:
        """
        转换每日资金流向数据

        Tushare 字段：
        - trade_date: 交易日期
        - hgt: 沪股通（百万元）
        - sgt: 深股通（百万元）
        - north_money: 北向资金（百万元）

        Args:
            raw_data: 原始数据

        Returns:
            转换后的数据
        """
        result = []
        for item in raw_data:
            # 日期格式转换：YYYYMMDD -> YYYY-MM-DD
            trade_date = str(item.get("trade_date", ""))
            date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"

            # 沪股通、深股通（百万元 -> 亿元）
            hgt = float(item.get("hgt", 0) or 0) / 100  # 百万元转亿元
            sgt = float(item.get("sgt", 0) or 0) / 100
            north_money = float(item.get("north_money", 0) or 0) / 100

            # 状态判断
            status = self._get_status(north_money)

            result.append({
                "date": date,
                "sh_flow": round(hgt, 2),
                "sz_flow": round(sgt, 2),
                "total_flow": round(north_money, 2),
                "status": status
            })

        # 按日期降序排列
        result.sort(key=lambda x: x["date"], reverse=True)

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
    import json

    # 导入数据源以触发注册
    from openclaw_alpha.data_sources import registry  # noqa: F401

    async def main():
        fetcher = FlowFetcherTushare()

        print("=== 测试每日净流入 ===")
        daily = await fetcher.fetch_daily()
        print(json.dumps(daily, ensure_ascii=False, indent=2))

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
