# -*- coding: utf-8 -*-
"""RSSHub 工具模块"""

from .fetcher import (
    RSSItem,
    fetch_all_routes,
    fetch_single_url,
    fetch_with_fallback,
    is_valid_feed,
    parse_date,
)
from .instances import INVESTMENT_ROUTES, RSSHUB_INSTANCES

__all__ = [
    # 实例配置
    "RSSHUB_INSTANCES",
    "INVESTMENT_ROUTES",
    # RSS 提取
    "RSSItem",
    "parse_date",
    "is_valid_feed",
    "fetch_single_url",
    "fetch_with_fallback",
    "fetch_all_routes",
]
