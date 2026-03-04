# -*- coding: utf-8 -*-
"""申万行业数据获取器"""

from openclaw_alpha.fetchers.sw_industry.models import (
    SwIndustryFetchParams,
    SwIndustryItem,
    SwIndustryFetchResult,
)
from openclaw_alpha.fetchers.sw_industry.tushare import (
    SwIndustryTushareFetcher,
)

__all__ = [
    "SwIndustryFetchParams",
    "SwIndustryItem",
    "SwIndustryFetchResult",
    "SwIndustryTushareFetcher",
]
