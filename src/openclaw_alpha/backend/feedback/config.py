# -*- coding: utf-8 -*-
"""用户反馈处理模块配置"""

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

    session_poll_timeout_seconds: int = 300
    result_wait_timeout_seconds: int = 600


class FeedbackConfig(BaseModel):
    """用户反馈处理模块配置"""

    enabled: bool = True
    interval_minutes: int = 30
    agent_id: str = "alpha"
    model: str | None = None
    delivery: DeliveryConfig = DeliveryConfig()
    cron: CronConfig = CronConfig()
    feedback_new_dir: str = "runtime/feedback/new"
    feedback_done_dir: str = "runtime/feedback/done"


def load_feedback_config() -> FeedbackConfig:
    """加载用户反馈处理模块配置（从 settings.feedback 读取）"""
    data = settings.feedback
    if not data:
        return FeedbackConfig()
    return FeedbackConfig(**data)
