# -*- coding: utf-8 -*-
"""涨跌停数据获取器"""

from .limit_fetcher import LimitFetcher

# 导入数据源模块以触发注册
from openclaw_alpha.data_sources import registry  # noqa: F401


async def fetch(date: str = None) -> dict:
    """
    获取涨跌停统计数据

    Args:
        date: 交易日期，格式 YYYY-MM-DD，默认今天

    Returns:
        涨跌停统计数据
    """
    fetcher = LimitFetcher()
    return await fetcher.fetch(date=date)
