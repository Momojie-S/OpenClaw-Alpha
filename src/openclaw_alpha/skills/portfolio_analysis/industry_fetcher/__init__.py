# -*- coding: utf-8 -*-
"""行业信息 Fetcher"""

from .industry_fetcher import IndustryInfoFetcher, IndustryInfo, fetch, get_fetcher
from . import akshare  # 导入以触发自动注册

__all__ = ["IndustryInfoFetcher", "IndustryInfo", "fetch", "get_fetcher"]
