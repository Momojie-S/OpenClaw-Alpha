# -*- coding: utf-8 -*-
"""限售解禁数据 Fetcher 模块"""

# 导入数据源注册（确保 AKShare 已注册）
from openclaw_alpha.data_sources import AkshareDataSource  # noqa: F401

from .restricted_release_fetcher import RestrictedReleaseFetcher

# 创建全局实例
_fetcher = RestrictedReleaseFetcher()


async def fetch(
    mode: str = "upcoming",
    start_date: str = "",
    end_date: str = "",
    symbol: str = "",
) -> dict:
    """
    获取限售解禁数据

    Args:
        mode: 模式，可选值：
            - "upcoming": 获取即将解禁的股票（默认）
            - "queue": 获取单只股票的解禁排期
            - "summary": 获取按日期汇总的解禁情况
        start_date: 开始日期 (YYYYMMDD)，upcoming/summary 模式需要
        end_date: 结束日期 (YYYYMMDD)，upcoming/summary 模式需要
        symbol: 股票代码，queue 模式需要

    Returns:
        数据字典，包含 mode、data 和 meta 字段
    """
    params = {
        "mode": mode,
        "start_date": start_date,
        "end_date": end_date,
        "symbol": symbol,
    }
    return await _fetcher.fetch(params)
