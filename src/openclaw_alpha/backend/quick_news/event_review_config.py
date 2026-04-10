# -*- coding: utf-8 -*-
"""事件回顾配置"""

from pathlib import Path

import yaml
from pydantic import BaseModel

from openclaw_alpha.core.path_utils import get_runtime_dir


class EventReviewConfig(BaseModel):
    """事件回顾配置"""

    enabled: bool = True
    schedule_time: str = "08:00"
    concurrency: int = 1
    agent_id: str = "main"
    model: str | None = None


def get_event_review_config_path() -> Path:
    """获取事件回顾配置文件路径"""
    return get_runtime_dir() / "config" / "event-review.yaml"


def load_event_review_config(config_path: Path | None = None) -> EventReviewConfig:
    """加载事件回顾配置"""
    config_path = config_path or get_event_review_config_path()

    if not config_path.exists():
        return EventReviewConfig()

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return EventReviewConfig(**data)
