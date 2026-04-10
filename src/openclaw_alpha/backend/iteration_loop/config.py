# -*- coding: utf-8 -*-
"""Iteration Loop 配置"""

from pydantic import BaseModel

from openclaw_alpha.core.settings import settings


class DevTasksConfig(BaseModel):
    """开发任务配置"""

    enabled: bool = True


class IterationLoopConfig(BaseModel):
    """Iteration Loop 主模块配置"""

    enabled: bool = True
    interval_minutes: int = 30
    dev_tasks: DevTasksConfig = DevTasksConfig()


def load_iteration_config() -> IterationLoopConfig:
    """加载 Iteration Loop 配置（从 settings 读取）"""
    data = settings._data.get("iteration_loop", {})
    if not data:
        return IterationLoopConfig()
    return IterationLoopConfig(**data)
