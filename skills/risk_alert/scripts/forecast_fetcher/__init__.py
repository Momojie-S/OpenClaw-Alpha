# -*- coding: utf-8 -*-
"""业绩预告 Fetcher"""

from openclaw_alpha.data_sources import registry  # noqa: F401

from .forecast_fetcher import ForecastFetcher

# 全局实例
_fetcher = ForecastFetcher()


async def fetch(date: str | None = None, risk_type: str | None = None) -> list[dict]:
    """
    获取业绩预告数据

    Args:
        date: 日期，格式 YYYY-MM-DD（可选）
        risk_type: 风险类型过滤（"高"或"中"）

    Returns:
        业绩预告列表
    """
    params = {}
    if date:
        params["date"] = date
    if risk_type:
        params["risk_type"] = risk_type

    return await _fetcher.fetch(params)
