# -*- coding: utf-8 -*-
"""用户反馈处理模块 - 工具函数"""

import json
import logging
from pathlib import Path

from openclaw_alpha.backend.feedback.task_executor import get_feedback_dir

logger = logging.getLogger(__name__)


def scan_pending_feedback(
    limit: int = 1,
    project_root: Path | None = None,
) -> list[Path]:
    """
    扫描待处理的反馈

    Args:
        limit: 最多返回多少条，0 表示全部
        project_root: 项目根目录

    Returns:
        待处理反馈文件列表
    """
    feedback_dir = get_feedback_dir(project_root, subdir="new")

    if not feedback_dir.exists():
        logger.warning(f"反馈目录不存在: {feedback_dir}")
        return []

    feedback_files = list(feedback_dir.glob("*.json"))

    pending_files = []
    for feedback_file in feedback_files:
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
