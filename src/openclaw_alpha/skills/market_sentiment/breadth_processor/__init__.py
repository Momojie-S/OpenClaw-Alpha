# -*- coding: utf-8 -*-
"""市场宽度处理器模块"""

from .breadth_processor import (
    process,
    _calc_health_level,
    _calc_trend,
    _detect_signals,
)

__all__ = [
    "process",
    "_calc_health_level",
    "_calc_trend",
    "_detect_signals",
]
