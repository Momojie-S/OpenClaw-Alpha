# -*- coding: utf-8 -*-
"""新闻模块定时任务"""

import asyncio
import logging

from openclaw_alpha.rsshub import INVESTMENT_ROUTES

from ..scheduler import Scheduler
from .config import NewsConfig, load_news_config
from .rss_fetcher import fetch_with_instance
from .state_manager import (
    add_pending,
    is_processed,
    load_state,
    mark_processed,
    save_state,
)

logger = logging.getLogger(__name__)


async def fetch_and_process(route: str) -> None:
    """
    拉取单个路由并处理新新闻（自动尝试多个实例）

    Args:
        route: RSS 路由（如 /cls/telegraph）
    """
    # 从路由提取 route_id
    route_id = route.strip("/").split("/")[0]
    logger.info(f"处理路由: {route} (route_id: {route_id})")

    # 1. 拉取 RSS（自动尝试多个实例）
    instance, items = await fetch_with_instance(route)

    if not items:
        logger.info(f"路由无新内容: {route}")
        return

    logger.info(f"成功从 {instance} 获取 {len(items)} 条新闻")

    # 2. 加载今日状态
    state = load_state(route_id)

    # 3. 过滤未处理的新闻
    from .models import NewsItem

    news_items = [
        NewsItem(
            id=item["id"],
            title=item["title"],
            link=item["link"],
            published=item.get("published"),
            summary=item.get("summary"),
        )
        for item in items
    ]
    new_items = [item for item in news_items if not is_processed(state, item.id)]

    if not new_items:
        logger.info(f"无新新闻: {route_id}")
        return

    logger.info(f"发现 {len(new_items)} 条新新闻: {route_id}")

    # 4. 处理新新闻（暂时只记录，不触发分析）
    for item in new_items:
        add_pending(state, item)
        logger.info(f"新新闻: {item.title}")

        # TODO: 触发分析任务
        # job_id = await submit_analysis(item)
        # mark_processed(state, item, job_id)

    # 5. 保存状态
    save_state(state)


async def fetch_all_sources() -> None:
    """拉取所有 RSS 路由"""
    config = load_news_config()

    if not config.enabled:
        logger.info("新闻模块已禁用")
        return

    logger.info(f"开始拉取 {len(INVESTMENT_ROUTES)} 个路由")

    for route in INVESTMENT_ROUTES:
        try:
            await fetch_and_process(route)
        except Exception as e:
            logger.error(f"处理路由失败: {route}, 错误: {e}")

    logger.info("RSS 拉取完成")


def setup_news_jobs(scheduler: Scheduler) -> None:
    """
    注册新闻模块定时任务

    Args:
        scheduler: 调度器实例
    """
    config = load_news_config()

    if not config.enabled:
        logger.info("新闻模块已禁用，跳过任务注册")
        return

    scheduler.add_interval_job(
        fetch_all_sources,
        job_id="news-fetch-all",
        minutes=config.interval_minutes,
    )

    logger.info(f"新闻任务已注册，间隔: {config.interval_minutes} 分钟")
