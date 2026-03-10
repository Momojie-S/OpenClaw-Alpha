# -*- coding: utf-8 -*-
"""涨停追踪数据类型"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any


class LimitUpType(str, Enum):
    """涨停类型"""
    LIMIT_UP = "limit_up"       # 涨停
    LIMIT_DOWN = "limit_down"   # 跌停
    BROKEN = "broken"           # 炸板
    PREVIOUS = "previous"       # 昨日涨停


@dataclass
class LimitUpItem:
    """涨停股数据"""
    code: str              # 股票代码
    name: str              # 股票名称
    change_pct: float      # 涨跌幅 %
    price: float           # 最新价
    amount: float          # 成交额（亿）
    float_mv: float        # 流通市值（亿）
    total_mv: float        # 总市值（亿）
    turnover_rate: float   # 换手率 %
    first_limit_time: str  # 首次封板时间
    last_limit_time: str   # 最后封板时间
    limit_times: int       # 当日炸板次数
    limit_stat: str        # 涨停统计
    continuous: int        # 连板数
    industry: str          # 所属行业

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LimitUpResult:
    """涨停追踪结果"""
    date: str
    limit_type: LimitUpType
    items: list[LimitUpItem]
    total: int
    continuous_stat: dict[int, int]  # {连板数: 数量}

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "limit_type": self.limit_type.value,
            "total": self.total,
            "continuous_stat": self.continuous_stat,
            "items": [item.to_dict() for item in self.items],
        }
