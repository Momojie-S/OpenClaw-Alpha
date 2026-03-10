# -*- coding: utf-8 -*-
"""ETF 数据获取"""

# 导入数据源以触发注册
from openclaw_alpha.data_sources import registry  # noqa: F401

from .etf_fetcher import EtfFetcher

# 全局实例
_fetcher = EtfFetcher()


async def fetch_spot() -> list:
    """获取全部 ETF 实时行情

    Returns:
        ETF 行情列表（EtfSpot 字典）

    Example:
        >>> spots = await fetch_spot()
        >>> print(f"共 {len(spots)} 只 ETF")
    """
    params = {"action": "spot"}
    result = await _fetcher.fetch(params)
    return result.get("data", [])


async def fetch_history(symbol: str, days: int = 30) -> list:
    """获取 ETF 历史数据

    Args:
        symbol: ETF 代码（如 sz159915）
        days: 历史天数

    Returns:
        历史数据列表（EtfHistory 字典）

    Example:
        >>> history = await fetch_history("sz159915", days=10)
        >>> print(f"共 {len(history)} 条数据")
    """
    params = {"action": "history", "symbol": symbol, "days": days}
    result = await _fetcher.fetch(params)
    return result.get("data", [])
