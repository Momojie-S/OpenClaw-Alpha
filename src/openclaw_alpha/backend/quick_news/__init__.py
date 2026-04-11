# -*- coding: utf-8 -*-
"""新闻快速分析模块"""

from .config import QuickNewsConfig, load_quick_news_config
from .jobs import (
    fetch_all_quick_news,
    fetch_all_sources,
    register_quick_news_tasks,
)
from .task_executor import (
    build_message,
    load_task_template,
    submit_analysis,
)

__all__ = [
    # 配置
    "QuickNewsConfig",
    "load_quick_news_config",
    # 定时任务
    "fetch_all_quick_news",
    "fetch_all_sources",
    "register_quick_news_tasks",
    # 任务执行器
    "load_task_template",
    "build_message",
    "submit_analysis",
]
