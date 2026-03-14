# -*- coding: utf-8 -*-
"""新闻快速分析模块定时任务"""

import asyncio
import logging

from openclaw_alpha.rsshub import INVESTMENT_ROUTES

from ..scheduler import Scheduler
from .config import QuickNewsConfig, load_quick_news_config
from .rss_fetcher import fetch_with_instance
from .state_manager import (
    add_pending,
    is_processed,
    load_state,
    mark_processed,
    save_state,
)

logger = logging.getLogger(__name__)


async def fetch_and_process(route: str) -> list:
    """
    拉取单个路由并返回未处理的新闻（不触发分析）

    Args:
        route: RSS 路由（如 /cls/telegraph）

    Returns:
        未处理的新新闻列表（携带 route_id）
    """
    from datetime import date

    # 从路由提取 route_id
    route_id = route.strip("/").split("/")[0]
    logger.info(f"拉取路由: {route} (route_id: {route_id})")

    # 1. 拉取 RSS（自动尝试多个实例）
    instance, items = await fetch_with_instance(route)

    if not items:
        logger.info(f"路由无新内容: {route}")
        return []

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
            route_id=route_id,  # 携带 route_id
        )
        for item in items
    ]

    # 4. 只处理今天发布的新闻
    today = date.today()
    today_items = [item for item in news_items if item.published and item.published.date() == today]

    if len(today_items) < len(news_items):
        logger.info(f"过滤出今天发布的新闻: {len(today_items)} / {len(news_items)}")

    # 5. 过滤未处理的
    new_items = [item for item in today_items if not is_processed(state, item.id)]

    if not new_items:
        logger.info(f"无新新闻: {route_id}")
        return []

    logger.info(f"发现 {len(new_items)} 条新新闻: {route_id}")

    # 只添加到待处理列表，不保存状态
    for item in new_items:
        add_pending(state, item)

    # 保存状态（记录待处理）
    save_state(state)

    return new_items


async def fetch_all_quick_news(limit: int = 1) -> None:
    """
    拉取所有 RSS 路由并触发分析任务

    Args:
        limit: 全局最多处理多少条新闻，默认 1（调试用），0 表示全部
    """
    config = load_quick_news_config()

    if not config.enabled:
        logger.info("新闻模块已禁用")
        return

    logger.info(f"开始拉取 {len(INVESTMENT_ROUTES)} 个路由 (全局 limit: {limit})")

    # 1. 收集所有路由的新新闻
    all_new_items = []
    for route in INVESTMENT_ROUTES:
        try:
            items = await fetch_and_process(route)
            all_new_items.extend(items)
        except Exception as e:
            logger.error(f"拉取路由失败: {route}, 错误: {e}")

    if not all_new_items:
        logger.info("无新新闻需要处理")
        return

    logger.info(f"总共发现 {len(all_new_items)} 条新新闻")

    # 2. 应用全局 limit 限制（limit=0 表示全部）
    if limit > 0:
        all_new_items = all_new_items[:limit]
        logger.info(f"应用全局 limit 限制，处理前 {limit} 条")

    logger.info(f"准备处理 {len(all_new_items)} 条新新闻")

    # 3. 逐个处理新新闻（触发分析任务）
    from .task_executor import submit_analysis

    for item in all_new_items:
        # 使用 item 携带的 route_id
        route_id = item.route_id
        if not route_id:
            logger.warning(f"item 缺少 route_id: {item.id}")
            continue

        # 加载对应路由的状态
        state = load_state(route_id)

        logger.info(f"处理新闻: {item.title} (route: {route_id})")

        # 触发快速分析任务
        job_id, task_dir, worth_deep_analysis = await submit_analysis(
            title=item.title,
            link=item.link,
            summary=item.summary or "",
        )

        # 标记已处理
        if job_id:
            mark_processed(state, item, job_id, str(task_dir))
            logger.info(f"快速分析任务已完成: {job_id}, 目录: {task_dir}, 值得深度分析: {worth_deep_analysis}")
        else:
            logger.warning(f"快速分析任务失败: {item.title}")

        # 保存状态
        save_state(state)

    logger.info("新闻处理完成")


def setup_quick_news_jobs(scheduler: Scheduler) -> None:
    """
    注册新闻模块定时任务

    Args:
        scheduler: 调度器实例
    """
    from functools import partial

    config = load_quick_news_config()

    if not config.enabled:
        logger.info("新闻模块已禁用，跳过任务注册")
        return

    # 定时任务处理所有新闻（limit=0）
    scheduler.add_interval_job(
        partial(fetch_all_quick_news, limit=0),
        job_id="news-fetch-all",
        minutes=config.interval_minutes,
    )

    logger.info(f"新闻任务已注册，间隔: {config.interval_minutes} 分钟")
