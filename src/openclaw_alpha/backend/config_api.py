# -*- coding: utf-8 -*-
"""配置管理 API 路由"""

import json
import logging
from typing import Any
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from openclaw_alpha.backend.iteration_loop.config import (
    IterationLoopConfig,
    DevTasksConfig,
    load_iteration_config,
)
from openclaw_alpha.backend.feedback.config import (
    FeedbackConfig,
    load_feedback_config,
)
from openclaw_alpha.core.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["config"])


def _get_config_path() -> Path:
    return settings.project_root / "runtime" / "config.json"


def _load_config_json() -> dict:
    return json.loads(_get_config_path().read_text(encoding="utf-8"))


def _save_config_json(data: dict) -> None:
    _get_config_path().write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


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
    """获取 Iteration Loop 配置"""
    try:
        return load_iteration_config()
    except Exception as e:
        logger.error(f"获取 Iteration Loop 配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.put("/iteration-loop", response_model=IterationLoopConfig)
async def update_iteration_loop_config(update: IterationLoopConfigUpdate):
    """更新 Iteration Loop 配置（部分更新）"""
    try:
        data = _load_config_json()
        il = data.get("iteration_loop", {})

        if update.enabled is not None:
            il["enabled"] = update.enabled
        if update.interval_minutes is not None:
            il["interval_minutes"] = update.interval_minutes
        if update.dev_tasks is not None:
            il["dev_tasks"] = update.dev_tasks.model_dump()

        data["iteration_loop"] = il
        _save_config_json(data)

        logger.info("Iteration Loop 配置已更新")
        return IterationLoopConfig(**il)

    except Exception as e:
        logger.error(f"更新 Iteration Loop 配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


# ============ Feedback Config API ============


@router.get("/feedback", response_model=FeedbackConfig)
async def get_feedback_config():
    """获取 Feedback 配置"""
    try:
        return load_feedback_config()
    except Exception as e:
        logger.error(f"获取 Feedback 配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.put("/feedback", response_model=FeedbackConfig)
async def update_feedback_config(update: FeedbackConfigUpdate):
    """更新 Feedback 配置（部分更新）"""
    try:
        data = _load_config_json()
        fb = data.get("feedback", {})

        if update.enabled is not None:
            fb["enabled"] = update.enabled
        if update.interval_minutes is not None:
            fb["interval_minutes"] = update.interval_minutes

        data["feedback"] = fb
        _save_config_json(data)

        logger.info("Feedback 配置已更新")
        return FeedbackConfig(**fb)

    except Exception as e:
        logger.error(f"更新 Feedback 配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")
