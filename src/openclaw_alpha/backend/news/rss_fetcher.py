# -*- coding: utf-8 -*-
"""新闻 RSS 拉取逻辑（适配 news 模块）"""

import logging

from openclaw_alpha.rsshub import RSSItem, fetch_with_fallback

logger = logging.getLogger(__name__)


async def fetch_rss(url: str) -> list[dict]:
    """
    拉取 RSS 源（兼容旧接口）

    Args:
        url: RSS 源 URL

    Returns:
        新闻列表（字典格式）
    """
    logger.info(f"开始拉取 RSS: {url}")

    # 从 URL 提取路由
    # URL 格式: https://instance.com/route
    parts = url.split("://")[-1].split("/", 1)
    if len(parts) < 2:
        logger.warning(f"无效的 RSS URL: {url}")
        return []

    route = "/" + parts[1]
    instance, items = fetch_with_fallback(route)

    if items:
        logger.info(f"拉取完成: {url}, 获取 {len(items)} 条新闻")
    else:
        logger.warning(f"拉取失败: {url}")

    # 转换为字典格式
    return [
        {
            "id": item.id,
            "title": item.title,
            "link": item.link,
            "published": item.published,
            "summary": item.summary,
        }
        for item in items
    ]


async def fetch_with_instance(route: str) -> tuple[str, list[dict]]:
    """
    尝试多个实例拉取同一路由（适配 news 模块）

    Args:
        route: RSS 路由（如 /cls/telegraph）

    Returns:
        (成功的实例域名, 新闻列表)
    """
    instance, items = fetch_with_fallback(route)

    # 转换为字典格式
    news_items = [
        {
            "id": item.id,
            "title": item.title,
            "link": item.link,
            "published": item.published,
            "summary": item.summary,
        }
        for item in items
    ]

    return (instance, news_items)
