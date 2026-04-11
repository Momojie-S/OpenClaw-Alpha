# -*- coding: utf-8 -*-
"""TaskQueue 单元测试"""

import asyncio
import json
import pytest
from pathlib import Path

from openclaw_alpha.backend.task_queue import TaskQueue, TaskRegistry, TaskQueueConfig


@pytest.fixture
def tmp_runtime(tmp_path):
    return tmp_path


@pytest.fixture
def registry():
    r = TaskRegistry()
    # 注册一些测试任务
    r.register("high", _make_task("high"), priority=1)
    r.register("medium", _make_task("medium"), priority=2)
    r.register("low", _make_task("low"), priority=3)
    return r


def _make_task(name: str):
    """创建一个记录调用次数的任务函数"""
    calls = {"count": 0}

    async def execute():
        calls["count"] += 1

    execute.calls = calls
    execute.name = name
    return execute


@pytest.fixture
def queue(tmp_runtime, registry):
    config = TaskQueueConfig(persistence_path="test_queue.json")
    return TaskQueue(config, registry, tmp_runtime)


@pytest.mark.asyncio
async def test_enqueue_dedup(queue):
    """同类型任务去重"""
    assert await queue.enqueue("high") is True
    assert await queue.enqueue("high") is False


@pytest.mark.asyncio
async def test_priority_order(tmp_runtime, registry):
    """优先级排序：高优先级先执行"""
    order = []

    async def record_high():
        order.append("high")

    async def record_low():
        order.append("low")

    registry._tasks["high"] = (record_high, 1)
    registry._tasks["low"] = (record_low, 3)

    config = TaskQueueConfig(persistence_path="test_queue.json")
    q = TaskQueue(config, registry, tmp_runtime)

    # 低优先级先入队
    await q.enqueue("low")
    await q.enqueue("high")

    await q.start()
    # 等待 worker 处理完
    await asyncio.sleep(0.2)
    await q.stop()

    assert order == ["high", "low"]


@pytest.mark.asyncio
async def test_persistence_write(tmp_runtime, queue):
    """入队后写入 persistence 文件"""
    await queue.enqueue("high")
    await queue.enqueue("low")

    data = json.loads((tmp_runtime / "test_queue.json").read_text())
    types = {t["type"] for t in data}
    assert types == {"high", "low"}


@pytest.mark.asyncio
async def test_persistence_restore(tmp_runtime, registry):
    """启动时从 persistence 恢复任务"""
    # 写入 persistence 文件
    persistence = tmp_runtime / "test_queue.json"
    persistence.write_text(json.dumps([
        {"type": "medium", "priority": 2, "enqueued_at": "2026-01-01T00:00:00+00:00"},
        {"type": "high", "priority": 1, "enqueued_at": "2026-01-01T00:00:00+00:00"},
    ]))

    config = TaskQueueConfig(persistence_path="test_queue.json")
    q = TaskQueue(config, registry, tmp_runtime)
    # start 会恢复 + 启动 worker
    await q.start()
    await asyncio.sleep(0.3)
    await q.stop()

    # 两个任务都应该被执行
    assert registry.get("high")[0].calls["count"] == 1
    assert registry.get("medium")[0].calls["count"] == 1


@pytest.mark.asyncio
async def test_failure_no_retry(tmp_runtime, registry):
    """执行失败不重试，继续处理下一个"""
    order = []

    async def fail_task():
        order.append("fail")
        raise RuntimeError("boom")

    async def ok_task():
        order.append("ok")

    registry._tasks["fail"] = (fail_task, 1)
    registry._tasks["ok"] = (ok_task, 2)

    config = TaskQueueConfig(persistence_path="test_queue.json")
    q = TaskQueue(config, registry, tmp_runtime)

    await q.enqueue("fail")
    await q.enqueue("ok")

    await q.start()
    await asyncio.sleep(0.3)
    await q.stop()

    assert order == ["fail", "ok"]


@pytest.mark.asyncio
async def test_unregistered_type(queue):
    """未注册的任务类型入队失败"""
    assert await queue.enqueue("nonexistent") is False
