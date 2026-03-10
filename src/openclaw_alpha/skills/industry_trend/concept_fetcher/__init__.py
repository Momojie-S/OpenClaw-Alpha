# -*- coding: utf-8 -*-
"""概念板块 Fetcher"""

# 导入数据源以触发注册
from openclaw_alpha.data_sources import registry  # noqa: F401

from .concept_fetcher import ConceptFetcher

# 全局实例
_fetcher = ConceptFetcher()


async def fetch(date: str = None) -> list[dict]:
    """获取概念板块数据
    
    Args:
        date: 日期（YYYY-MM-DD），默认当日
    
    Returns:
        概念板块数据列表
    
    Example:
        >>> data = await fetch("2026-03-06")
        >>> print(data[0])
        {
            'name': 'AI',
            'code': 'BK0001',
            'date': '2026-03-06',
            'metrics': {
                'close': 1234.56,
                'pct_change': 3.5,
                'amount': 120000,  # 万元
                'turnover_rate': 8.2,
                'float_mv': 500000,  # 万元
                'up_count': 45,
                'down_count': 12,
            }
        }
    """
    from datetime import datetime
    
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    return await _fetcher.fetch({"date": date})
