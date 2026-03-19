# -*- coding: utf-8 -*-
"""配置管理 API 路由"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from openclaw_alpha.backend.iteration_loop.config import (
    IterationLoopConfig,
    DevTasksConfig,
    load_iteration_config,
    get_config_path as get_iteration_config_path,
)
from openclaw_alpha.backend.feedback.config import (
    FeedbackConfig,
    load_feedback_config,
    get_feedback_config_path,
)
import yaml

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["config"])


# ============ Models ============


class IterationLoopConfigUpdate(BaseModel):
    """Iteration Loop 配置更新请求"""

    enabled: bool | None = None
    interval_minutes: int | None = None
    dev_tasks: DevTasksConfig | None = None


class FeedbackConfigUpdate(BaseModel):
    """Feedback 配置更新请求"""

    enabled: bool | None = None
    interval_minutes: int | None = None


# ============ Iteration Loop Config API ============


@router.get("/iteration-loop", response_model=IterationLoopConfig)
async def get_iteration_loop_config():
    """
    获取 Iteration Loop 配置
    """
    try:
        config = load_iteration_config()
        return config
    except Exception as e:
        logger.error(f"获取 Iteration Loop 配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.put("/iteration-loop", response_model=IterationLoopConfig)
async def update_iteration_loop_config(update: IterationLoopConfigUpdate):
    """
    更新 Iteration Loop 配置（部分更新）

    支持更新：
    - enabled: 主开关
    - interval_minutes: 执行间隔（分钟）
    - dev_tasks.enabled: 开发任务开关
    """
    try:
        # 读取现有配置
        config_path = get_iteration_config_path()
        current_config = load_iteration_config()

        # 转换为字典
        config_dict = current_config.model_dump()

        # 合并更新
        if update.enabled is not None:
            config_dict["enabled"] = update.enabled
        if update.interval_minutes is not None:
            config_dict["interval_minutes"] = update.interval_minutes
        if update.dev_tasks is not None:
            config_dict["dev_tasks"] = update.dev_tasks.model_dump()

        # 写入文件
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False)

        logger.info(f"Iteration Loop 配置已更新: {config_path}")

        # 返回更新后的配置
        return IterationLoopConfig(**config_dict)

    except Exception as e:
        logger.error(f"更新 Iteration Loop 配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


# ============ Feedback Config API ============


@router.get("/feedback", response_model=FeedbackConfig)
async def get_feedback_config():
    """
    获取 Feedback 配置
    """
    try:
        config = load_feedback_config()
        return config
    except Exception as e:
        logger.error(f"获取 Feedback 配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.put("/feedback", response_model=FeedbackConfig)
async def update_feedback_config(update: FeedbackConfigUpdate):
    """
    更新 Feedback 配置（部分更新）

    支持更新：
    - enabled: 主开关
    - interval_minutes: 执行间隔（分钟）
    """
    try:
        # 读取现有配置
        config_path = get_feedback_config_path()
        current_config = load_feedback_config()

        # 转换为字典
        config_dict = current_config.model_dump()

        # 合并更新
        if update.enabled is not None:
            config_dict["enabled"] = update.enabled
        if update.interval_minutes is not None:
            config_dict["interval_minutes"] = update.interval_minutes

        # 写入文件
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False)

        logger.info(f"Feedback 配置已更新: {config_path}")

        # 返回更新后的配置
        return FeedbackConfig(**config_dict)

    except Exception as e:
        logger.error(f"更新 Feedback 配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")
