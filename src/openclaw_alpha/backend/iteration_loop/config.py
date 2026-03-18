# -*- coding: utf-8 -*-
"""Iteration Loop 配置"""

from pathlib import Path

import yaml
from pydantic import BaseModel

from openclaw_alpha.core.path_utils import get_workspace_dir


class IterationLoopConfig(BaseModel):
    """Iteration Loop 主模块配置"""

    enabled: bool = True
    interval_minutes: int = 30


def get_config_path() -> Path:
    """获取配置文件路径"""
    return get_workspace_dir() / "iteration_loop" / "config.yaml"


def load_iteration_config(config_path: Path | None = None) -> IterationLoopConfig:
    """
    加载 Iteration Loop 配置

    Args:
        config_path: 配置文件路径（None 则使用默认路径）

    Returns:
        配置对象
    """
    config_path = config_path or get_config_path()

    if not config_path.exists():
        return IterationLoopConfig()

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return IterationLoopConfig(**data)
