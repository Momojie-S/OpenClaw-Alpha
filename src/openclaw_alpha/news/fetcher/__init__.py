# -*- coding: utf-8 -*-
"""新闻数据 Fetcher"""

from .models import NewsItem, NewsResult
from .news_fetcher import fetch

__all__ = ["fetch", "NewsItem", "NewsResult"]
