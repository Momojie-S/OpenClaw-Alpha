# -*- coding: utf-8 -*-
"""期权数据 Fetcher 入口"""

import asyncio
from typing import Optional

from openclaw_alpha.core.fetcher import Fetcher, FetchMethod
from openclaw_alpha.data_sources.akshare import AkshareDataSource


class OptionDataFetcher(Fetcher):
    """期权数据获取入口"""

    name = "option_data"

    def __init__(self):
        super().__init__()
        # 注册 AKShare 实现
        self.register(OptionDataFetcherAkshare())


class OptionDataFetcherAkshare(FetchMethod):
    """AKShare 期权数据获取实现"""

    name = "option_data_akshare"
    required_data_source = "akshare"
    priority = 10

    def __init__(self):
        super().__init__()

    async def fetch(
        self,
        data_type: str,
        underlying: Optional[str] = None,
        date: Optional[str] = None,
        exchange: Optional[str] = None
    ) -> dict:
        """
        获取期权数据

        Args:
            data_type: 数据类型
                - "daily_stats_sse": 上交所每日统计
                - "daily_stats_szse": 深交所每日统计
                - "risk_indicator": 期权风险指标
                - "finance_board": 金融期权行情
            underlying: 标的代码（如 510050）
            date: 日期（格式：YYYY-MM-DD）
            exchange: 交易所（sse/szse/cffex）

        Returns:
            期权数据字典
        """
        client = await self.get_client()

        # 转换日期格式
        trade_date = date.replace("-", "") if date else None

        if data_type == "daily_stats_sse":
            # 上交所每日统计
            df = client.option_daily_stats_sse(date=trade_date)
            return df.to_dict("records") if df is not None and not df.empty else []

        elif data_type == "daily_stats_szse":
            # 深交所每日统计
            df = client.option_daily_stats_szse(date=trade_date)
            return df.to_dict("records") if df is not None and not df.empty else []

        elif data_type == "risk_indicator":
            # 期权风险指标（需要标的代码）
            if not underlying:
                raise ValueError("risk_indicator 需要 underlying 参数")
            df = client.option_risk_indicator_sse(symbol=underlying)
            return self._transform_risk_indicator(df)

        elif data_type == "finance_board":
            # 金融期权行情
            df = client.option_finance_board(symbol=underlying or "华夏上证50ETF期权")
            return df.to_dict("records") if df is not None and not df.empty else []

        else:
            raise ValueError(f"不支持的数据类型: {data_type}")

    def _transform_risk_indicator(self, df) -> dict:
        """转换风险指标数据"""
        if df is None or df.empty:
            return {}

        # 提取关键指标
        result = {
            "greeks": [],
            "iv_stats": {
                "atm_iv": None,
                "iv_high": None,
                "iv_low": None
            }
        }

        for _, row in df.iterrows():
            greek_data = {
                "strike": row.get("行权价"),
                "delta": row.get("DELTA_VALUE"),
                "gamma": row.get("GAMMA_VALUE"),
                "vega": row.get("VEGA_VALUE"),
                "theta": row.get("THETA_VALUE"),
                "iv": row.get("IMPLC_VOLATLTY"),
                "type": row.get("合约类型")
            }
            result["greeks"].append(greek_data)

        # 计算平值附近的 IV 统计
        if result["greeks"]:
            ivs = [g["iv"] for g in result["greeks"] if g["iv"] and g["iv"] > 0]
            if ivs:
                result["iv_stats"]["atm_iv"] = sum(ivs) / len(ivs)
                result["iv_stats"]["iv_high"] = max(ivs)
                result["iv_stats"]["iv_low"] = min(ivs)

        return result


# 全局实例
_fetcher = OptionDataFetcher()


async def fetch(
    data_type: str,
    underlying: Optional[str] = None,
    date: Optional[str] = None,
    exchange: Optional[str] = None
) -> dict:
    """
    获取期权数据

    Args:
        data_type: 数据类型
        underlying: 标的代码
        date: 日期
        exchange: 交易所

    Returns:
        期权数据
    """
    return await _fetcher.fetch(
        data_type=data_type,
        underlying=underlying,
        date=date,
        exchange=exchange
    )
