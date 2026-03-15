# -*- coding: utf-8 -*-
"""新闻快速分析模块配置"""

from pathlib import Path

import yaml
from pydantic import BaseModel

from openclaw_alpha.core.path_utils import get_workspace_dir


class DeliveryConfig(BaseModel):
    """消息推送配置"""

    recipients: list[str] = ["Momojie"]  # 推送目标列表
    channel: str = "wecom"  # 推送渠道

    @property
    def to(self) -> str:
        """cron 任务的单一接收人（取 recipients 第一个）"""
        return self.recipients[0] if self.recipients else "Momojie"


class CronConfig(BaseModel):
    """Cron 任务配置"""

    # 轮询 session store 的超时时间（秒）
    session_poll_timeout_seconds: int = 300

    # 等待 report.md 创建的超时时间（秒）
    report_wait_timeout_seconds: int = 300


class QuickNewsConfig(BaseModel):
    """新闻快速分析模块配置"""

    enabled: bool = True
    interval_minutes: int = 30
    agent_id: str = "alpha"
    model: str | None = None
    delivery: DeliveryConfig = DeliveryConfig()
    cron: CronConfig = CronConfig()


def get_quick_news_config_path() -> Path:
    """获取新闻快速分析配置文件路径"""
    return get_workspace_dir() / "quick_news" / "config.yaml"


def load_quick_news_config(config_path: Path | None = None) -> QuickNewsConfig:
    """
    加载新闻快速分析模块配置

    Args:
        config_path: 配置文件路径（None 则使用默认路径）

    Returns:
        新闻快速分析模块配置对象
    """
    config_path = config_path or get_quick_news_config_path()

    if not config_path.exists():
        return QuickNewsConfig()

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return QuickNewsConfig(**data)


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
