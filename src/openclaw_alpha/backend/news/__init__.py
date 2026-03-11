# -*- coding: utf-8 -*-
"""新闻订阅模块"""

from .config import NewsConfig, load_news_config
from .jobs import fetch_all_sources, fetch_and_process, setup_news_jobs
from .models import NewsItem, NewsItemState, NewsState
from .rss_fetcher import fetch_rss, fetch_with_instance
from .state_manager import cleanup_old_states, load_state, save_state
from .task_executor import (
    build_message,
    generate_news_id,
    load_task_template,
    submit_analysis,
)

__all__ = [
    # 配置
    "NewsConfig",
    "load_news_config",
    # 模型
    "NewsItem",
    "NewsItemState",
    "NewsState",
    # RSS 拉取
    "fetch_rss",
    "fetch_with_instance",
    # 状态管理
    "load_state",
    "save_state",
    "cleanup_old_states",
    # 定时任务
    "fetch_all_sources",
    "fetch_and_process",
    "setup_news_jobs",
    # 任务执行器
    "load_task_template",
    "build_message",
    "generate_news_id",
    "submit_analysis",
]
