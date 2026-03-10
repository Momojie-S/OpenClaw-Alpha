# -*- coding: utf-8 -*-
"""估值数据数据模型"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ValuationData:
    """估值数据"""

    date: str  # 日期
    value: Optional[float] = None  # 指标值

    def to_dict(self) -> dict:
        """转换为字典"""
        return {"date": self.date, "value": self.value}
