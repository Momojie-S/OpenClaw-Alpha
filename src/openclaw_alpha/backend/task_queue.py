# -*- coding: utf-8 -*-
"""统一任务队列：优先级调度 + 单并发约束 + 持久化"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Awaitable

from .config import TaskQueueConfig

logger = logging.getLogger(__name__)

# 全局队列引用，供模块的 scheduler trigger lambda 使用
_global_queue: TaskQueue | None = None


class TaskRegistry:
    """任务类型注册表"""

    def __init__(self) -> None:
        self._tasks: dict[str, tuple[Callable[[], Awaitable[None]], int]] = {}

    def register(self, task_type: str, fn: Callable[[], Awaitable[None]], priority: int) -> None:
        """注册任务类型及其执行函数和优先级（数值越小优先级越高）"""
        self._tasks[task_type] = (fn, priority)

    def get(self, task_type: str) -> tuple[Callable[[], Awaitable[None]], int] | None:
        """获取执行函数和优先级"""
        return self._tasks.get(task_type)


class TaskQueue:
    """统一任务队列，单并发约束"""

    def __init__(self, config: TaskQueueConfig, registry: TaskRegistry, runtime_dir: Path) -> None:
        self._queue: asyncio.PriorityQueue[tuple[int, str]] = asyncio.PriorityQueue()
        self._persistence = runtime_dir / config.persistence_path
        self._registry = registry
        self._worker_task: asyncio.Task[None] | None = None
        self._enqueued_types: set[str] = set()  # 内存去重集合

    async def start(self) -> None:
        """启动 worker 协程 + 从 persistence 恢复任务"""
        await self._restore()
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("TaskQueue worker 已启动")

    async def stop(self) -> None:
        """优雅停止 worker"""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            logger.info("TaskQueue worker 已停止")

    async def enqueue(self, task_type: str) -> bool:
        """入队（去重）。已存在同 type → 返回 False"""
        if task_type in self._enqueued_types:
            logger.debug(f"任务已存在，跳过入队: {task_type}")
            return False

        entry = self._registry.get(task_type)
        if entry is None:
            logger.error(f"未注册的任务类型: {task_type}")
            return False

        _, priority = entry
        self._enqueued_types.add(task_type)
        await self._queue.put((priority, task_type))
        self._persist_append(task_type, priority)
        logger.info(f"任务已入队: {task_type} (priority={priority})")
        return True

    async def _worker(self) -> None:
        """消费循环：get → execute → remove from persistence"""
        while True:
            try:
                priority, task_type = await self._queue.get()
            except asyncio.CancelledError:
                break

            try:
                entry = self._registry.get(task_type)
                if entry is None:
                    logger.error(f"任务类型未找到: {task_type}")
                    continue

                fn, _ = entry
                logger.info(f"开始执行任务: {task_type}")
                await fn()
                logger.info(f"任务执行完成: {task_type}")
            except Exception as e:
                logger.error(f"任务执行失败: {task_type} - {e}", exc_info=True)
            finally:
                self._enqueued_types.discard(task_type)
                self._persist_remove(task_type)
                self._queue.task_done()

    # ---- persistence ----

    def _read_persistence(self) -> list[dict[str, Any]]:
        if not self._persistence.exists():
            return []
        try:
            return json.loads(self._persistence.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"读取 persistence 失败: {e}")
            return []

    def _write_persistence(self, tasks: list[dict[str, Any]]) -> None:
        self._persistence.parent.mkdir(parents=True, exist_ok=True)
        self._persistence.write_text(
            json.dumps(tasks, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _persist_append(self, task_type: str, priority: int) -> None:
        tasks = self._read_persistence()
        tasks.append({
            "type": task_type,
            "priority": priority,
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
        })
        self._write_persistence(tasks)

    def _persist_remove(self, task_type: str) -> None:
        tasks = self._read_persistence()
        tasks = [t for t in tasks if t["type"] != task_type]
        self._write_persistence(tasks)

    async def _restore(self) -> None:
        """从 persistence 恢复未执行任务"""
        tasks = self._read_persistence()
        if not tasks:
            return

        # 按优先级排序后入队
        tasks.sort(key=lambda t: t.get("priority", 99))
        for t in tasks:
            task_type = t["type"]
            if task_type in self._enqueued_types:
                continue
            entry = self._registry.get(task_type)
            if entry is None:
                logger.warning(f"恢复跳过未注册任务: {task_type}")
                continue
            self._enqueued_types.add(task_type)
            self._queue.put_nowait((t.get("priority", entry[1]), task_type))
            logger.info(f"恢复任务: {task_type}")

        logger.info(f"从 persistence 恢复了 {len(tasks)} 个任务")
