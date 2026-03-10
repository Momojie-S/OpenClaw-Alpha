# -*- coding: utf-8 -*-
"""资金流向数据获取器 - AKShare 实现"""


import akshare as ak

from openclaw_alpha.core.fetcher import FetchMethod


class FlowFetcherAkshare(FetchMethod):
    """
    资金流向数据获取器 - AKShare 实现

    使用 AKShare 的大盘资金流向接口
    """

    name = "flow_akshare"
    required_data_source = "akshare"
    priority = 10

    def _call_api(self, date: str = None) -> dict:
        """
        调用 AKShare API 获取数据

        Args:
            date: 日期，格式 YYYY-MM-DD

        Returns:
            原始 API 响应
        """
        # 获取大盘资金流向数据
        df = ak.stock_market_fund_flow()

        # 筛选指定日期或获取最近一天
        if date:
            target_df = df[df["日期"] == date]
            if not target_df.empty:
                latest = target_df.iloc[0]
            else:
                # 如果指定日期没有数据，返回最近一天
                latest = df.iloc[-1]
        else:
            # 没有指定日期，返回最近一天
            latest = df.iloc[-1]

        # 转换日期为字符串
        date_value = latest["日期"]
        date_str = (
            date_value.strftime("%Y-%m-%d")
            if hasattr(date_value, "strftime")
            else str(date_value)
        )

        return {
            "date": date_str,
            "main_net_inflow": float(latest["主力净流入-净额"]),
            "main_net_inflow_pct": float(latest["主力净流入-净占比"]),
            "retail_net_inflow": float(latest["小单净流入-净额"]),
            "retail_net_inflow_pct": float(latest["小单净流入-净占比"]),
        }

    def _transform(self, raw_data: dict) -> dict:
        """
        转换数据格式

        Args:
            raw_data: 原始 API 响应

        Returns:
            标准化的资金流向数据
        """
        return raw_data

    async def fetch(self, date: str = None) -> dict:
        """
        获取资金流向数据

        Args:
            date: 日期，格式 YYYY-MM-DD

        Returns:
            资金流向数据
        """
        raw_data = self._call_api(date=date)
        return self._transform(raw_data)


if __name__ == "__main__":
    # 直接测试
    method = FlowFetcherAkshare()
    raw_data = method._call_api(date="2026-03-06")
    print(f"原始数据: {raw_data}")

    result = method._transform(raw_data)
    print(f"转换后: {result}")
