# -*- coding: utf-8 -*-
"""FastAPI 入口"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import load_config
from openclaw_alpha.core.logger import setup_logging
from .scheduler import Scheduler
from .task_queue import TaskQueue, TaskRegistry, _global_queue
from openclaw_alpha.core.path_utils import get_runtime_dir
from openclaw_alpha.openclaw.gateway_client import (
    get_gateway_client,
    close_gateway_client,
)


logger = logging.getLogger(__name__)

# 全局调度器
scheduler: Scheduler | None = None
# 全局任务队列
task_queue: TaskQueue | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    config = load_config()
    setup_logging(log_level=config.log_level)

    logger.info("服务启动中...")

    # 连接 Gateway 客户端
    try:
        client = await get_gateway_client()
        logger.info(f"Gateway 客户端已连接: {client.config.url}")
    except Exception as e:
        logger.warning(f"Gateway 客户端连接失败: {e}（将在需要时重连）")

    # 启动调度器
    global scheduler, task_queue
    scheduler = Scheduler(config.scheduler)
    scheduler.start()

    # 创建任务队列和注册表
    registry = TaskRegistry()
    runtime_dir = get_runtime_dir()
    task_queue = TaskQueue(config.task_queue, registry, runtime_dir)

    # 设置全局引用（供 scheduler trigger lambda 使用）
    import openclaw_alpha.backend.task_queue as tq_module
    tq_module._global_queue = task_queue

    # 注册模块任务
    if config.modules.get("quick_news", {}).get("enabled"):
        from .quick_news.jobs import register_quick_news_tasks

        register_quick_news_tasks(registry, scheduler)

    # 注册 Iteration Loop 任务
    from .iteration_loop.jobs import register_iteration_tasks

    register_iteration_tasks(registry, scheduler)

    # 启动 worker
    await task_queue.start()

    logger.info(f"服务已启动，监听 {config.host}:{config.port}")

    yield

    # 关闭时
    logger.info("服务关闭中...")
    if task_queue:
        await task_queue.stop()
    if scheduler:
        scheduler.shutdown()

    # 关闭 Gateway 客户端
    await close_gateway_client()

    logger.info("服务已关闭")


from .config_api import router as config_router


app = FastAPI(
    title="OpenClaw-Alpha Backend",
    description="OpenClaw-Alpha Web 服务",
    version="0.1.0",
    lifespan=lifespan,
)

# 注册配置管理 API
app.include_router(config_router)


def get_scheduler() -> Scheduler | None:
    """获取调度器实例"""
    return scheduler


# ============ API Models ============


# ============ API Endpoints ============


@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "service": "OpenClaw-Alpha Backend"}
