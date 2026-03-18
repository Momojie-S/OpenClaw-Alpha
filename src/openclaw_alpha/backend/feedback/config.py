# -*- coding: utf-8 -*-
"""用户反馈处理模块配置"""

from pathlib import Path

import yaml
from pydantic import BaseModel

from openclaw_alpha.core.path_utils import get_workspace_dir


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

    # 轮询 session store 的超时时间（秒）
    session_poll_timeout_seconds: int = 300

    # 等待 decision 字段的超时时间（秒）
    result_wait_timeout_seconds: int = 300


class FeedbackConfig(BaseModel):
    """用户反馈处理模块配置"""

    enabled: bool = True
    interval_minutes: int = 30
    agent_id: str = "alpha"
    model: str | None = None
    delivery: DeliveryConfig = DeliveryConfig()
    cron: CronConfig = CronConfig()


def get_feedback_config_path() -> Path:
    """获取用户反馈处理模块配置文件路径"""
    return get_workspace_dir() / "feedback" / "config.yaml"


def load_feedback_config(config_path: Path | None = None) -> FeedbackConfig:
    """
    加载用户反馈处理模块配置

    Args:
        config_path: 配置文件路径（None 则使用默认路径）

    Returns:
        用户反馈处理模块配置对象
    """
    config_path = config_path or get_feedback_config_path()

    if not config_path.exists():
        return FeedbackConfig()

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return FeedbackConfig(**data)
