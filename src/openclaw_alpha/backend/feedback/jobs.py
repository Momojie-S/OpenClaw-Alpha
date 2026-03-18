# -*- coding: utf-8 -*-
"""用户反馈处理模块定时任务"""

import asyncio
import json
import logging
from pathlib import Path

from openclaw_alpha.backend.feedback.config import load_feedback_config
from openclaw_alpha.backend.feedback.task_executor import (
    _notify_maintainers,
    get_feedback_dir,
    submit_feedback_task,
)

logger = logging.getLogger(__name__)


def scan_pending_feedback(
    limit: int = 1,
    project_root: Path | None = None,
) -> list[Path]:
    """
    扫描待处理的反馈

    Args:
        limit: 最多处理多少条反馈，0 表示全部
        project_root: 项目根目录

    Returns:
        待处理反馈文件列表
    """
    feedback_dir = get_feedback_dir(project_root, subdir="new")

    if not feedback_dir.exists():
        logger.warning(f"反馈目录不存在: {feedback_dir}")
        return []

    # 扫描所有 JSON 文件（new/ 目录下，无子目录）
    feedback_files = list(feedback_dir.glob("*.json"))

    # 过滤 pending 状态
    pending_files = []
    for feedback_file in feedback_files:
        try:
            with open(feedback_file, "r", encoding="utf-8") as f:
                feedback = json.load(f)

            if feedback.get("status") == "pending":
                pending_files.append(feedback_file)
        except json.JSONDecodeError as e:
            logger.error(f"解析反馈文件失败: {feedback_file}, {e}")
        except Exception as e:
            logger.error(f"读取反馈文件失败: {feedback_file}, {e}")

    # 应用 limit 限制
    if limit > 0:
        pending_files = pending_files[:limit]

    return pending_files


async def process_feedback(limit: int = 1, project_root: Path | None = None) -> None:
    """
    处理用户反馈

    Args:
        limit: 最多处理多少条反馈，0 表示全部
        project_root: 项目根目录
    """
    config = load_feedback_config()

    if not config.enabled:
        logger.info("反馈模块已禁用")
        return

    logger.info(f"开始扫描反馈 (limit: {limit})")

    # 扫描待处理反馈
    pending_files = scan_pending_feedback(limit, project_root)

    if not pending_files:
        logger.info("无待处理反馈")
        return

    logger.info(f"发现 {len(pending_files)} 条待处理反馈")

    # 逐个处理
    success_count = 0
    for feedback_file in pending_files:
        try:
            with open(feedback_file, "r", encoding="utf-8") as f:
                feedback = json.load(f)

            logger.info(f"处理反馈: {feedback['id']}")

            # 触发处理任务
            success = await submit_feedback_task(feedback_file, feedback)

            if success:
                success_count += 1
            else:
                logger.warning(f"反馈处理失败: {feedback['id']}")

        except Exception as e:
            logger.error(f"处理反馈异常: {feedback_file}, {e}")

    logger.info(f"反馈处理完成，成功: {success_count}/{len(pending_files)}")


async def _send_new_feedback_notification(feedback_files: list[Path], config) -> None:
    """
    发送新反馈通知给维护者

    Args:
        feedback_files: 反馈文件列表
        config: 模块配置
    """
    recipients = config.delivery.recipients

    if not recipients:
        return

    # 读取反馈内容
    feedbacks = []
    for feedback_file in feedback_files:
        try:
            with open(feedback_file, "r", encoding="utf-8") as f:
                feedback = json.load(f)
                feedbacks.append(feedback)
        except Exception as e:
            logger.error(f"读取反馈文件失败: {feedback_file}, {e}")

    if not feedbacks:
        return

    # 构造消息
    message = f"💬 收到 {len(feedbacks)} 条新反馈\n\n"

    for i, feedback in enumerate(feedbacks[:5], 1):  # 最多显示 5 条
        content = feedback.get("content", "")[:50]
        source_user = feedback.get("source_user", "系统")
        source_channel = feedback.get("source_channel", "")
        source_info = f"{source_user} ({source_channel})" if source_channel else source_user
        message += f"{i}. {source_info}\n"
        message += f"   {content}{'...' if len(feedback.get('content', '')) > 50 else ''}\n"
        message += f"   ID: {feedback['id']}\n\n"

    if len(feedbacks) > 5:
        message += f"... 还有 {len(feedbacks) - 5} 条\n\n"

    message += "💡 处理完成后会再次通知"

    try:
        from openclaw_alpha.openclaw.gateway_client import get_gateway_client

        client = await get_gateway_client()
        for recipient in recipients:
            result = await client.send_message(
                channel=recipient.channel,
                to=recipient.name,
                message=message,
                account_id=recipient.agent_id,
            )
            if result.get("ok"):
                logger.info(f"新反馈通知已发送: {recipient.name}")
            else:
                logger.warning(f"新反馈通知发送失败: {recipient.name}")
    except Exception as e:
        logger.error(f"发送新反馈通知失败: {e}")


async def scan_and_notify(limit: int = 1, project_root: Path | None = None) -> None:
    """
    扫描反馈并发送通知

    Args:
        limit: 最多处理多少条反馈，0 表示全部
        project_root: 项目根目录
    """
    config = load_feedback_config()

    if not config.enabled:
        logger.info("反馈模块已禁用")
        return

    # 扫描待处理反馈
    pending_files = scan_pending_feedback(limit, project_root)

    if not pending_files:
        return

    # 发送新反馈通知
    await _send_new_feedback_notification(pending_files, config)


def setup_feedback_jobs(scheduler, project_root: Path | None = None) -> None:
    """
    注册反馈处理模块定时任务

    Args:
        scheduler: 调度器实例
        project_root: 项目根目录
    """
    from functools import partial

    from openclaw_alpha.backend.feedback.task_executor import check_completed_feedback

    config = load_feedback_config()

    if not config.enabled:
        logger.info("反馈模块已禁用，跳过任务注册")
        return

    # 定时处理反馈（limit=0 表示全部）
    scheduler.add_interval_job(
        partial(process_feedback, limit=0, project_root=project_root),
        job_id="feedback-process",
        minutes=config.interval_minutes,
    )

    # 定时检测已完成反馈（发送通知 + 归档）
    scheduler.add_interval_job(
        partial(check_completed_feedback, project_root=project_root),
        job_id="feedback-check-completed",
        minutes=5,  # 每 5 分钟检测一次
    )

    logger.info(f"反馈处理任务已注册，间隔: {config.interval_minutes} 分钟")
    logger.info("反馈完成检测任务已注册，间隔: 5 分钟")
