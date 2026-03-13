# -*- coding: utf-8 -*-
"""FastAPI 入口"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import load_config
from .logger import setup_logging
from .scheduler import Scheduler


logger = logging.getLogger(__name__)

# 全局调度器
scheduler: Scheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    config = load_config()
    setup_logging(log_level=config.log_level)

    logger.info("服务启动中...")

    # 启动调度器
    global scheduler
    scheduler = Scheduler(config.scheduler)
    scheduler.start()

    # 注册模块任务
    if config.modules.get("quick_news", {}).get("enabled"):
        from .quick_news.jobs import setup_quick_news_jobs

        setup_quick_news_jobs(scheduler)

    logger.info(f"服务已启动，监听 {config.host}:{config.port}")

    yield

    # 关闭时
    logger.info("服务关闭中...")
    if scheduler:
        scheduler.shutdown()
    logger.info("服务已关闭")


app = FastAPI(
    title="OpenClaw-Alpha Backend",
    description="OpenClaw-Alpha Web 服务",
    version="0.1.0",
    lifespan=lifespan,
)


def get_scheduler() -> Scheduler | None:
    """获取调度器实例"""
    return scheduler


# ============ API Models ============


class TriggerQuickNewsResponse(BaseModel):
    """触发新闻快速分析响应"""

    success: bool
    message: str
    routes_processed: int
    limit: int | None = None


# ============ API Endpoints ============


@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "service": "OpenClaw-Alpha Backend"}


@app.post("/api/quick-news/trigger", response_model=TriggerQuickNewsResponse)
async def trigger_quick_news_fetch(limit: int = 1):
    """
    手动触发新闻快速分析任务

    立即执行一次所有配置的 RSS 路由拉取和分析任务

    主要用途：调试

    Query Parameters:
        limit: 全局最多处理多少条新闻，默认 1（调试用）
    """
    try:
        from .quick_news.jobs import fetch_all_sources
        from .quick_news.config import load_quick_news_config
        from openclaw_alpha.rsshub import INVESTMENT_ROUTES

        # 检查是否启用
        config = load_quick_news_config()
        if not config.enabled:
            raise HTTPException(status_code=400, detail="新闻快速分析模块已禁用")

        # 执行拉取任务
        logger.info(f"手动触发新闻快速分析任务 (limit: {limit})")
        await fetch_all_sources(limit)

        return TriggerQuickNewsResponse(
            success=True,
            message="新闻快速分析任务已执行",
            routes_processed=len(INVESTMENT_ROUTES),
            limit=limit,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"手动触发新闻快速分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")
