# -*- coding: utf-8 -*-
"""新闻数据获取 Fetcher

支持的数据源：
- 财联社全球资讯（推荐）
- 东方财富个股新闻
"""

from .news_fetcher import fetch

__all__ = ["fetch"]
