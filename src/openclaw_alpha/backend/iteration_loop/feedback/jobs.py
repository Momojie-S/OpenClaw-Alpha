# -*- coding: utf-8 -*-
"""用户反馈处理子模块 - process 接口"""

import json
import logging
from pathlib import Path

from openclaw_alpha.backend.feedback.config import load_feedback_config
from openclaw_alpha.backend.feedback.task_executor import submit_feedback_task

logger = logging.getLogger(__name__)


def _scan_pending(limit: int = 1, project_root: Path | None = None) -> list[Path]:
    """
    扫描待处理的反馈

    Args:
        limit: 最多返回多少条，0 表示全部
        project_root: 项目根目录

    Returns:
        待处理反馈文件列表
    """
    from openclaw_alpha.backend.feedback.task_executor import get_feedback_dir

    feedback_dir = get_feedback_dir(project_root, subdir="new")

    if not feedback_dir.exists():
        return []

    pending_files = []
    for feedback_file in feedback_dir.glob("*.json"):
        try:
            with open(feedback_file, "r", encoding="utf-8") as f:
                feedback = json.load(f)

            if feedback.get("status") == "pending":
                pending_files.append(feedback_file)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"读取反馈文件失败: {feedback_file}, {e}")

    if limit > 0:
        pending_files = pending_files[:limit]

    return pending_files


async def process(limit: int = 1, project_root: Path | None = None) -> bool:
    """
    处理指定数量的反馈

    Args:
        limit: 最多处理的反馈数
        project_root: 项目根目录

    Returns:
        是否有反馈被处理
    """
    config = load_feedback_config()

    if not config.enabled:
        return False

    pending_files = _scan_pending(limit, project_root)

    if not pending_files:
        return False

    for feedback_file in pending_files:
        try:
            with open(feedback_file, "r", encoding="utf-8") as f:
                feedback = json.load(f)

            logger.info(f"处理反馈: {feedback['id']}")
            success = await submit_feedback_task(feedback_file, feedback)

            if success:
                return True  # 处理了一个任务就返回
            else:
                logger.warning(f"反馈处理失败: {feedback['id']}")

        except Exception as e:
            logger.error(f"处理反馈异常: {feedback_file}, {e}")

    return False
