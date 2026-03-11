# -*- coding: utf-8 -*-
"""RSS 文章提取工具"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime

import feedparser

from .instances import RSSHUB_INSTANCES

logger = logging.getLogger(__name__)


@dataclass
class RSSItem:
    """
    RSS 文章

    Attributes:
        id: 文章唯一标识
        title: 文章标题
        link: 文章链接
        published: 发布时间
        summary: 文章内容（feedparser 标准字段名，对应 RSSHub JSON Feed 的 content_html）
        
            实际内容取决于数据源：
            - 完整正文（部分源）
            - 摘要（大多数源）
            - 简短内容（快讯类）
            
            示例：
            - wallstreetcn/news: 248 字符（摘要 + 免责声明）
            - jin10: 279 字符（较详细的摘要）
    """

    id: str
    title: str
    link: str
    published: datetime | None = None
    summary: str | None = None


def parse_date(date_str: str | None) -> datetime | None:
    """
    解析日期字符串

    Args:
        date_str: 日期字符串

    Returns:
        datetime 对象或 None
    """
    if not date_str:
        return None

    try:
        from email.utils import parsedate_to_datetime

        return parsedate_to_datetime(date_str)
    except Exception:
        return None


def is_valid_feed(feed: feedparser.FeedParserDict) -> bool:
    """
    检查 RSS feed 是否有效

    Args:
        feed: feedparser 解析结果

    Returns:
        是否有效
    """
    # 检查是否有条目
    if not feed.entries:
        return False

    # 检查是否包含 RSSHub 的限制提示
    feed_content = str(feed)
    if "rsshub.app is intended for testing" in feed_content:
        return False

    return True


def fetch_single_url(url: str) -> list[RSSItem]:
    """
    从单个 URL 拉取 RSS

    Args:
        url: RSS 源 URL

    Returns:
        RSS 文章列表
    """
    logger.debug(f"尝试拉取: {url}")

    try:
        feed = feedparser.parse(url)

        if not is_valid_feed(feed):
            logger.debug(f"无效的 RSS feed: {url}")
            return []

        items = []
        for entry in feed.entries:
            # 生成唯一 ID
            item_id = entry.get("id") or entry.get("guid")
            if not item_id:
                # 使用 link hash 作为 ID
                item_id = hashlib.md5(entry.link.encode()).hexdigest()

            # 获取 summary 字段（feedparser 标准字段名）
            # 对应 RSSHub JSON Feed 的 content_html
            # 实际内容可能是完整正文、摘要、或简短内容（取决于数据源）
            summary = entry.get("summary")

            items.append(
                RSSItem(
                    id=item_id,
                    title=entry.get("title", ""),
                    link=entry.get("link", ""),
                    published=parse_date(entry.get("published")),
                    summary=summary,
                )
            )

        logger.debug(f"拉取成功: {url}, 获取 {len(items)} 条")
        return items

    except Exception as e:
        logger.debug(f"拉取失败: {url}, 错误: {e}")
        return []


def fetch_with_fallback(
    route: str, instances: list[str] | None = None
) -> tuple[str, list[RSSItem]]:
    """
    尝试多个实例拉取同一路由，直到成功

    Args:
        route: RSS 路由（如 /cls/telegraph）
        instances: 实例列表（None 则使用默认实例）

    Returns:
        (成功的实例域名, RSS 文章列表)
    """
    instances = instances or RSSHUB_INSTANCES

    for instance in instances:
        url = f"{instance}{route}"
        items = fetch_single_url(url)

        if items:
            # 提取实例域名
            domain = instance.replace("https://", "").replace("http://", "")
            return (domain, items)

    logger.warning(f"所有实例均失败: {route}")
    return ("", [])


def fetch_all_routes(
    routes: list[str], instances: list[str] | None = None
) -> dict[str, tuple[str, list[RSSItem]]]:
    """
    拉取多个路由

    Args:
        routes: 路由列表
        instances: 实例列表（None 则使用默认实例）

    Returns:
        路由 -> (成功实例, 文章列表) 的映射
    """
    results = {}

    for route in routes:
        instance, items = fetch_with_fallback(route, instances)
        results[route] = (instance, items)
        logger.info(f"路由 {route}: 从 {instance} 获取 {len(items)} 条")

    return results
