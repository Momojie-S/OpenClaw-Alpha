# -*- coding: utf-8 -*-
"""配置加载模块"""

from pathlib import Path
from typing import Any

import yaml

from pydantic import BaseModel


# 默认配置目录
DEFAULT_CONFIG_DIR = Path.home() / ".openclaw_alpha" / "config"


class SchedulerConfig(BaseModel):
    """调度器配置"""

    enabled: bool = True
    timezone: str = "Asia/Shanghai"


class ModuleConfig(BaseModel):
    """模块配置"""

    enabled: bool = True


class ServiceConfig(BaseModel):
    """服务配置"""

    host: str = "0.0.0.0"
    port: int = 8765
    log_level: str = "INFO"
    scheduler: SchedulerConfig = SchedulerConfig()
    modules: dict[str, Any] = {}


def load_config(config_path: Path | None = None) -> ServiceConfig:
    """
    加载服务配置

    Args:
        config_path: 配置文件路径（None 则使用默认路径）

    Returns:
        服务配置对象
    """
    config_path = config_path or DEFAULT_CONFIG_DIR / "service.yaml"

    if not config_path.exists():
        # 返回默认配置
        return ServiceConfig()

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return ServiceConfig(**data)
