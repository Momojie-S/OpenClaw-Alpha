# -*- coding: utf-8 -*-
"""交易日历工具"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache

import pandas as pd


class MarketStatus(Enum):
    """市场状态枚举"""
    CLOSED = "休市"           # 非交易日
    PRE_MARKET = "盘前"       # 交易日 9:15 之前
    CALL_AUCTION = "集合竞价"  # 9:15-9:30
    MORNING = "早盘"          # 9:30-11:30
    LUNCH_BREAK = "午间休市"  # 11:30-13:00
    AFTERNOON = "午盘"        # 13:00-15:00
    AFTER_HOURS = "收盘"      # 15:00 之后


@dataclass
class TradingCalendarContext:
    """交易日历上下文"""
    current_time: datetime          # 当前时间
    is_trading_day: bool           # 是否为交易日
    is_trading_time: bool          # 是否为交易时段
    market_status: str             # 市场状态
    suggested_date: str            # 建议使用的日期
    previous_trading_day: str      # 上一个交易日
    next_trading_day: str          # 下一个交易日


# 全局缓存：交易日列表（避免重复请求）
_trading_days_cache: set[str] | None = None


def _load_trading_days() -> set[str]:
    """加载交易日列表（从 AKShare 获取）

    使用缓存机制，只请求一次。

    Returns:
        交易日集合（YYYY-MM-DD 格式）
    """
    global _trading_days_cache

    if _trading_days_cache is not None:
        return _trading_days_cache

    try:
        import akshare as ak
        # 获取历史交易日历
        df = ak.tool_trade_date_hist_sina()
        # 转换为集合，便于快速查找
        # AKShare 返回的格式是 YYYY-MM-DD
        _trading_days_cache = set(df['trade_date'].astype(str).tolist())
        return _trading_days_cache
    except Exception as e:
        # 如果获取失败，返回 None，回退到简单判断（仅排除周末）
        print(f"警告：无法获取交易日历数据，回退到简单判断（仅排除周末）: {e}")
        return set()


def get_trading_days(start_date: str | datetime, end_date: str | datetime) -> list[str]:
    """获取日期范围内的所有交易日

    Args:
        start_date: 开始日期（YYYY-MM-DD 或 datetime）
        end_date: 结束日期（YYYY-MM-DD 或 datetime）

    Returns:
        交易日列表（YYYY-MM-DD 格式）
    """
    if isinstance(start_date, datetime):
        start_date = start_date.strftime("%Y-%m-%d")
    if isinstance(end_date, datetime):
        end_date = end_date.strftime("%Y-%m-%d")

    trading_days_set = _load_trading_days()

    if not trading_days_set:
        # 回退：返回排除周末的所有日期
        result = []
        current = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        while current <= end:
            if current.weekday() < 5:  # 排除周末
                result.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
        return result

    # 从缓存中筛选
    result = []
    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        if date_str in trading_days_set:
            result.append(date_str)
        current += timedelta(days=1)

    return result


def is_trading_day(date: str | datetime | None = None) -> bool:
    """判断是否为交易日（含节假日判断）

    Args:
        date: 日期（YYYY-MM-DD 或 datetime），默认今天

    Returns:
        是否为交易日
    """
    if date is None:
        date = datetime.now()
    elif isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d")

    date_str = date.strftime("%Y-%m-%d")
    trading_days_set = _load_trading_days()

    if not trading_days_set:
        # 回退：仅排除周末
        return date.weekday() < 5

    return date_str in trading_days_set


def get_previous_trading_day(date: str | datetime | None = None) -> str:
    """获取上一个交易日

    Args:
        date: 起始日期（YYYY-MM-DD 或 datetime），默认今天

    Returns:
        上一个交易日（YYYY-MM-DD 格式）
    """
    if date is None:
        date = datetime.now()
    elif isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d")

    # 向前查找（最多查找 30 天）
    check_date = date - timedelta(days=1)
    max_attempts = 30
    attempts = 0

    while attempts < max_attempts:
        if is_trading_day(check_date):
            return check_date.strftime("%Y-%m-%d")
        check_date -= timedelta(days=1)
        attempts += 1

    # 未找到，返回 check_date（兜底）
    return check_date.strftime("%Y-%m-%d")


def get_next_trading_day(date: str | datetime | None = None) -> str:
    """获取下一个交易日

    Args:
        date: 起始日期（YYYY-MM-DD 或 datetime），默认今天

    Returns:
        下一个交易日（YYYY-MM-DD 格式）
    """
    if date is None:
        date = datetime.now()
    elif isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d")

    # 向后查找（最多查找 30 天）
    check_date = date + timedelta(days=1)
    max_attempts = 30
    attempts = 0

    while attempts < max_attempts:
        if is_trading_day(check_date):
            return check_date.strftime("%Y-%m-%d")
        check_date += timedelta(days=1)
        attempts += 1

    # 未找到，返回 check_date（兜底）
    return check_date.strftime("%Y-%m-%d")


def is_trading_time(time: datetime | None = None) -> bool:
    """判断是否为交易时段

    交易时段定义：
    - 集合竞价：9:15-9:30
    - 早盘：9:30-11:30
    - 午盘：13:00-15:00

    Args:
        time: 时间，默认当前时间

    Returns:
        是否为交易时段
    """
    if time is None:
        time = datetime.now()

    # 先判断是否为交易日
    if not is_trading_day(time):
        return False

    # 判断是否在交易时段
    current_time = time.time()
    from datetime import time as time_type

    # 集合竞价 + 早盘 + 午盘
    morning_call_start = time_type(9, 15)
    morning_call_end = time_type(11, 30)
    afternoon_start = time_type(13, 0)
    afternoon_end = time_type(15, 0)

    return (morning_call_start <= current_time <= morning_call_end or
            afternoon_start <= current_time <= afternoon_end)


def get_market_status(time: datetime | None = None) -> str:
    """获取市场状态

    Args:
        time: 时间，默认当前时间

    Returns:
        市场状态（休市/盘前/集合竞价/早盘/午间休市/午盘/收盘）
    """
    if time is None:
        time = datetime.now()

    # 非交易日
    if not is_trading_day(time):
        return MarketStatus.CLOSED.value

    # 判断交易时段
    current_time = time.time()
    from datetime import time as time_type

    # 盘前：9:15 之前
    if current_time < time_type(9, 15):
        return MarketStatus.PRE_MARKET.value
    # 集合竞价：9:15-9:30
    elif time_type(9, 15) <= current_time < time_type(9, 30):
        return MarketStatus.CALL_AUCTION.value
    # 早盘：9:30-11:30
    elif time_type(9, 30) <= current_time < time_type(11, 30):
        return MarketStatus.MORNING.value
    # 午间休市：11:30-13:00
    elif time_type(11, 30) <= current_time < time_type(13, 0):
        return MarketStatus.LUNCH_BREAK.value
    # 午盘：13:00-15:00
    elif time_type(13, 0) <= current_time < time_type(15, 0):
        return MarketStatus.AFTERNOON.value
    # 收盘：15:00 之后
    else:
        return MarketStatus.AFTER_HOURS.value


def get_suggested_date(time: datetime | None = None) -> str:
    """根据当前时间判断应使用的交易日期

    规则：
    - 交易日 9:30 之前：使用上一个交易日
    - 交易日 9:30 之后：使用当天
    - 非交易日：使用上一个交易日

    Args:
        time: 时间，默认当前时间

    Returns:
        交易日期（YYYY-MM-DD 格式）
    """
    if time is None:
        time = datetime.now()

    current_date = time.strftime("%Y-%m-%d")

    # 非交易日，返回上一个交易日
    if not is_trading_day(time):
        return get_previous_trading_day(time)

    # 交易日，判断是否已开盘
    from datetime import time as time_type
    if time.time() < time_type(9, 30):
        # 开盘前，返回上一个交易日
        return get_previous_trading_day(time)
    else:
        # 已开盘，返回当天
        return current_date


def get_trading_calendar_context(time: datetime | None = None) -> TradingCalendarContext:
    """获取完整的交易日历上下文

    Args:
        time: 时间，默认当前时间

    Returns:
        交易日历上下文
    """
    if time is None:
        time = datetime.now()

    return TradingCalendarContext(
        current_time=time,
        is_trading_day=is_trading_day(time),
        is_trading_time=is_trading_time(time),
        market_status=get_market_status(time),
        suggested_date=get_suggested_date(time),
        previous_trading_day=get_previous_trading_day(time),
        next_trading_day=get_next_trading_day(time),
    )


# ============== 保留旧接口，向后兼容 ==============

def get_trading_date_for_now() -> str:
    """根据当前时间判断应使用的交易日期（向后兼容）

    - 交易日 9:30 之前：使用上一个交易日
    - 交易日 9:30 之后：使用当天
    - 非交易日：使用上一个交易日

    Returns:
        交易日期（YYYY-MM-DD 格式）
    """
    return get_suggested_date()

