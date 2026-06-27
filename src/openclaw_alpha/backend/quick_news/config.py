# -*- coding: utf-8 -*-
"""新闻快速分析模块配置"""

from pydantic import BaseModel

from openclaw_alpha.core.settings import settings


class RecipientConfig(BaseModel):
    """单个接收人配置"""

    name: str
    agent_id: str = "notify"
    channel: str = "wecom"


class DeliveryConfig(BaseModel):
    """消息推送配置"""

    recipients: list[RecipientConfig] = [RecipientConfig(name="Momojie")]


class CronConfig(BaseModel):
    """Cron 任务配置"""

    agent_turn_timeout_seconds: int = 900
    session_poll_timeout_seconds: int = 900


class QuickNewsConfig(BaseModel):
    """新闻快速分析模块配置"""

    enabled: bool = True
    interval_minutes: int = 30
    deep_analysis_interval_minutes: int = 60
    agent_id: str = "main"
    model: str | None = None
    delivery: DeliveryConfig = DeliveryConfig()
    cron: CronConfig = CronConfig()
    fetch_limit: int = 0


def load_quick_news_config() -> QuickNewsConfig:
    """加载新闻快速分析配置（从 settings.quick_news 读取）"""
    data = settings.quick_news
    if not data:
        return QuickNewsConfig()
    return QuickNewsConfig(**data)
