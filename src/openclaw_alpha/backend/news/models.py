# -*- coding: utf-8 -*-
"""新闻模块数据模型"""

from datetime import datetime
from pydantic import BaseModel


class NewsItem(BaseModel):
    """单条新闻"""

    id: str
    title: str
    link: str
    published: datetime | None = None
    summary: str | None = None


class NewsItemState(BaseModel):
    """新闻状态"""

    id: str
    title: str
    link: str
    published: str | None = None
    processed: bool = False
    processed_at: str | None = None
    job_id: str | None = None
    workspace_dir: str | None = None


class NewsState(BaseModel):
    """新闻状态文件"""

    date: str
    route_id: str
    items: list[NewsItemState] = []
