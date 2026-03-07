# -*- coding: utf-8 -*-
"""资金流向数据获取器"""

from .flow_fetcher import FlowFetcher

# 导入数据源模块以触发注册
from openclaw_alpha.data_sources import registry  # noqa: F401


async def fetch(date: str = None) -> dict:
    """
    获取大盘资金流向数据

    Args:
        date: 交易日期，格式 YYYY-MM-DD，默认最近

    Returns:
        资金流向数据
    """
    fetcher = FlowFetcher()
    return await fetcher.fetch(date=date)
