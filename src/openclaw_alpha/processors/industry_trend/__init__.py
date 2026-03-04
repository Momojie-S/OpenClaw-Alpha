# -*- coding: utf-8 -*-
"""产业趋势分析加工器"""

from openclaw_alpha.processors.industry_trend.models import (
    IndustryTrendProcessParams,
    IndustryTrendProcessResult,
)
from openclaw_alpha.processors.industry_trend.processor import (
    IndustryTrendProcessor,
)

__all__ = [
    "IndustryTrendProcessParams",
    "IndustryTrendProcessResult",
    "IndustryTrendProcessor",
]
