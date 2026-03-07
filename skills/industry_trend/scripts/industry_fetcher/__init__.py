# -*- coding: utf-8 -*-
"""申万行业数据获取"""

# 导入数据源以触发注册
from openclaw_alpha.data_sources import registry  # noqa: F401

from .industry_fetcher import IndustryFetcher

# 全局实例
_fetcher = IndustryFetcher()


async def fetch(category: str = "L1", date: str = None) -> list[dict]:
    """获取申万行业数据
    
    Args:
        category: 行业层级（L1/L2/L3），默认 L1
        date: 日期（YYYY-MM-DD），默认当日
    
    Returns:
        行业数据列表
    """
    from datetime import datetime
    
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    params = {
        "category": category,
        "date": date,
    }
    
    return await _fetcher.fetch(params)
