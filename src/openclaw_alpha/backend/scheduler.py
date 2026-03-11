# -*- coding: utf-8 -*-
"""APScheduler 封装"""

import logging
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .config import SchedulerConfig


logger = logging.getLogger(__name__)


class Scheduler:
    """调度器封装"""

    def __init__(self, config: SchedulerConfig):
        """
        初始化调度器

        Args:
            config: 调度器配置
        """
        self.config = config
        self.scheduler: AsyncIOScheduler | None = None

    def start(self) -> None:
        """启动调度器"""
        if not self.config.enabled:
            logger.info("调度器已禁用，跳过启动")
            return

        self.scheduler = AsyncIOScheduler(timezone=self.config.timezone)
        self.scheduler.start()
        logger.info(f"调度器已启动，时区: {self.config.timezone}")

    def shutdown(self) -> None:
        """关闭调度器"""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("调度器已关闭")

    def add_interval_job(
        self,
        func: Callable,
        job_id: str,
        *,
        minutes: int = 30,
        replace_existing: bool = True,
    ) -> None:
        """
        添加间隔任务

        Args:
            func: 任务函数
            job_id: 任务 ID
            minutes: 间隔分钟数
            replace_existing: 是否替换已存在的任务
        """
        if not self.scheduler:
            logger.warning("调度器未启动，无法添加任务")
            return

        self.scheduler.add_job(
            func,
            trigger=IntervalTrigger(minutes=minutes),
            id=job_id,
            replace_existing=replace_existing,
        )
        logger.info(f"已添加间隔任务: {job_id}，间隔: {minutes} 分钟")

    def remove_job(self, job_id: str) -> None:
        """
        移除任务

        Args:
            job_id: 任务 ID
        """
        if not self.scheduler:
            return

        self.scheduler.remove_job(job_id)
        logger.info(f"已移除任务: {job_id}")
