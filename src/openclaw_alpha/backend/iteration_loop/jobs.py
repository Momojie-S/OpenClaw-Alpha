# -*- coding: utf-8 -*-
"""Iteration Loop 主循环逻辑"""

import logging
from pathlib import Path

from .config import IterationLoopConfig, load_iteration_config

logger = logging.getLogger(__name__)


async def run_iteration_cycle(project_root: Path | None = None) -> None:
    """
    主循环：持续处理直到无待办任务

    按优先级遍历子模块，每个子模块每次只处理一个任务（limit=1）。
    处理完一个任务后，重新从头遍历（给高优先级模块机会）。
    所有模块都没有任务时退出。
    """
    from .feedback import process as feedback_process

    # 子模块列表（按优先级排序）
    modules = [
        ("dev_tasks", _dev_tasks_process),  # 空壳，待实现
        ("feedback", feedback_process),
    ]

    while True:
        worked = False
        for name, process_fn in modules:
            try:
                if await process_fn(limit=1, project_root=project_root):
                    worked = True
                    logger.debug(f"模块 {name} 处理了一个任务，重新循环")
                    break  # 重新从头遍历
            except Exception as e:
                logger.error(f"模块 {name} 处理异常: {e}", exc_info=True)
                # 一个模块失败不影响其他模块，继续遍历

        if not worked:
            logger.debug("所有模块无待办任务，退出循环")
            break


async def _dev_tasks_process(
    limit: int = 1,
    project_root: Path | None = None,
) -> bool:
    """
    开发任务模块（空壳，待实现）

    Args:
        limit: 最多处理的任务数
        project_root: 项目根目录

    Returns:
        是否有任务被处理
    """
    # TODO: 实现开发任务处理
    return False


def setup_iteration_jobs(scheduler, project_root: Path | None = None) -> None:
    """
    注册 Iteration Loop 定时任务

    Args:
        scheduler: 调度器实例
        project_root: 项目根目录
    """
    from functools import partial

    config = load_iteration_config()

    if not config.enabled:
        logger.info("Iteration Loop 已禁用，跳过任务注册")
        return

    scheduler.add_interval_job(
        partial(run_iteration_cycle, project_root=project_root),
        job_id="iteration-loop",
        minutes=config.interval_minutes,
    )

    logger.info(f"Iteration Loop 已注册，间隔: {config.interval_minutes} 分钟")
