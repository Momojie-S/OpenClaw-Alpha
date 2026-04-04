# -*- coding: utf-8 -*-
"""新闻数据模型"""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class NewsItem:
    """新闻条目"""
    news_id: str
    title: str
    content: str
    date: str
    time: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None


@dataclass
class NewsResult:
    """新闻获取结果"""
    news: list[NewsItem] = field(default_factory=list)
    total: int = 0
    source: str = ""
