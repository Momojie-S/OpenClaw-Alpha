# -*- coding: utf-8 -*-
"""新闻快速分析模块配置"""

from pathlib import Path

import yaml
from pydantic import BaseModel

from openclaw_alpha.core.path_utils import get_runtime_dir


class RecipientConfig(BaseModel):
    """单个接收人配置"""

    name: str
    agent_id: str = "notify"  # 推送时使用的 agent ID
    channel: str = "wecom"  # 推送渠道


class DeliveryConfig(BaseModel):
    """消息推送配置"""

    recipients: list[RecipientConfig] = [RecipientConfig(name="Momojie")]


class CronConfig(BaseModel):
    """Cron 任务配置"""

    # Agent 执行超时（秒），传给 cron payload 的 timeoutSeconds
    agent_turn_timeout_seconds: int = 900

    # 轮询 Gateway cron job 完成状态的超时时间（秒）
    # 包括 Agent 执行 + delivery announce 的全部时间
    session_poll_timeout_seconds: int = 900


class QuickNewsConfig(BaseModel):
    """新闻快速分析模块配置"""

    enabled: bool = True
    interval_minutes: int = 30
    agent_id: str = "main"
    model: str | None = None
    delivery: DeliveryConfig = DeliveryConfig()
    cron: CronConfig = CronConfig()


def get_quick_news_config_path() -> Path:
    """获取新闻快速分析配置文件路径"""
    return get_runtime_dir() / "quick_news" / "config.yaml"


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



