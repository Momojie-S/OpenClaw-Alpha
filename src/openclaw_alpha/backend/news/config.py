# -*- coding: utf-8 -*-
"""新闻模块配置"""

from pathlib import Path

import yaml
from pydantic import BaseModel

from openclaw_alpha.rsshub import INVESTMENT_ROUTES

# 默认配置目录
DEFAULT_CONFIG_DIR = Path.home() / ".openclaw_alpha" / "config"


class NewsConfig(BaseModel):
    """新闻模块配置"""

    enabled: bool = True
    interval_minutes: int = 30


def load_news_config(config_path: Path | None = None) -> NewsConfig:
    """
    加载新闻模块配置

    Args:
        config_path: 配置文件路径（None 则使用默认路径）

    Returns:
        新闻模块配置对象
    """
    config_path = config_path or DEFAULT_CONFIG_DIR / "news.yaml"

    if not config_path.exists():
        # 返回默认配置
        return NewsConfig()

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return NewsConfig(**data)


def extract_route_id(url: str) -> str:
    """
    从 RSSHub URL 中提取 route_id

    Args:
        url: RSSHub URL

    Returns:
        route_id（路由路径的第一段）

    Examples:
        >>> extract_route_id("https://rsshub.app/cls/telegraph")
        'cls'
        >>> extract_route_id("https://rsshub.app/jin10")
        'jin10'
    """
    # 移除协议和域名，获取路径
    path = url.split("://")[-1]
    parts = path.split("/")

    # 找到第一个非空段（跳过域名）
    for i, part in enumerate(parts):
        if "." in part:  # 域名部分
            continue
        if part:  # 第一个非域名的非空段
            return part

    # 如果无法提取，使用 URL hash
    import hashlib

    return hashlib.md5(url.encode()).hexdigest()[:8]
