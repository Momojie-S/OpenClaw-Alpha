# -*- coding: utf-8 -*-
"""涨跌停数据获取器 - AKShare 实现"""

from datetime import datetime

import akshare as ak

from openclaw_alpha.core.fetcher import FetchMethod


class LimitFetcherAkshare(FetchMethod):
    """
    涨跌停数据获取器 - AKShare 实现

    使用 AKShare 的涨停股池和炸板股池接口
    """

    name = "limit_akshare"
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
        # 转换日期格式
        date_str = date.replace("-", "") if date else datetime.now().strftime("%Y%m%d")

        # 获取涨停股池
        limit_up_df = ak.stock_zt_pool_em(date=date_str)

        # 获取炸板股池
        try:
            break_df = ak.stock_zt_pool_zbgc_em(date=date_str)
            break_count = len(break_df)
        except Exception:
            break_count = 0

        return {
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "limit_up_df": limit_up_df,
            "break_count": break_count,
        }

    def _transform(self, raw_data: dict) -> dict:
        """
        转换数据格式

        Args:
            raw_data: 原始 API 响应

        Returns:
            标准化的涨跌停数据
        """
        limit_up_df = raw_data["limit_up_df"]

        return {
            "date": raw_data["date"],
            "limit_up": len(limit_up_df),
            "limit_down": 0,  # AKShare 没有跌停股池接口
            "break_board": raw_data["break_count"],
        }

    async def fetch(self, date: str = None) -> dict:
        """
        获取涨跌停数据

        Args:
            date: 日期，格式 YYYY-MM-DD

        Returns:
            涨跌停统计数据
        """
        raw_data = self._call_api(date=date)
        return self._transform(raw_data)


if __name__ == "__main__":
    # 直接测试，不使用 asyncio
    method = LimitFetcherAkshare()

    # 直接调用 _call_api 测试
    raw_data = method._call_api(date="2026-03-06")
    print(f"原始数据: limit_up={len(raw_data['limit_up_df'])}, break={raw_data['break_count']}")

    # 测试转换
    result = method._transform(raw_data)
    print(f"转换后: {result}")
