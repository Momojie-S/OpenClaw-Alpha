# -*- coding: utf-8 -*-
"""新闻快速分析模块定时任务

Backend 通过 CLI service 层拉取新闻，用 news.json 的 analysis_status 追踪分析状态。
"""

import asyncio
import json
import logging
import time
from pathlib import Path

from ...core.path_utils import get_runtime_dir
from ..scheduler import Scheduler
from .config import QuickNewsConfig, load_quick_news_config
from .task_executor import submit_analysis

logger = logging.getLogger(__name__)

# RSSHub 路由 → CLI source 名称 映射
_ROUTE_TO_SOURCE = {
    "/cls/telegraph": "cls_telegraph",
    "/jin10": "jin10",
    "/wallstreetcn/news": "wallstreetcn_news",
    "/yicai/brief": "yicai_brief",
}

_DEFAULT_DATA_DIR = get_runtime_dir() / "data"


def _scan_pending_news(data_dir: Path | None = None) -> list[dict]:
    """扫描 data/news/ 下所有待分析新闻。

    筛选条件：analysis_status 为空或 "failed"。
    返回按 created_at 排序（旧新闻优先）。
    """
    base = (data_dir or _DEFAULT_DATA_DIR) / "news"
    if not base.exists():
        return []

    pending = []
    for news_dir in base.iterdir():
        if not news_dir.is_dir():
            continue
        news_json = news_dir / "news.json"
        if not news_json.exists():
            continue
        try:
            data = json.loads(news_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        status = data.get("analysis_status")
        if status in (None, "failed"):
            pending.append(data)

    # 旧新闻优先（created_at 升序）
    pending.sort(key=lambda n: n.get("created_at", 0))
    return pending


async def fetch_all_sources() -> dict:
    """拉取所有新闻源并落盘。

    Returns:
        {"sources": int, "saved": int, "skipped": int}
    """
    from openclaw_alpha.news.service import fetch_and_save

    total_saved = 0
    total_skipped = 0
    source_count = 0

    for route, source_name in _ROUTE_TO_SOURCE.items():
        try:
            logger.info(f"拉取新闻源: {source_name} ({route})")
            result = await fetch_and_save(source=source_name, limit=100, data_dir=_DEFAULT_DATA_DIR)
            saved = result.get("saved", 0)
            skipped = result.get("skipped", 0)
            total_saved += saved
            total_skipped += skipped
            source_count += 1
            logger.info(f"  {source_name}: saved={saved}, skipped={skipped}")
        except Exception as e:
            logger.error(f"拉取新闻源失败: {source_name}, 错误: {e}")

    logger.info(f"拉取完成: {source_count} 个源, saved={total_saved}, skipped={total_skipped}")
    return {"sources": source_count, "saved": total_saved, "skipped": total_skipped}


async def fetch_all_quick_news(limit: int = 1) -> None:
    """拉取所有新闻源并触发分析任务。

    Args:
        limit: 全局最多分析多少条新闻，默认 1（调试用），0 表示全部
    """
    from openclaw_alpha.news.service import read_news_json, write_news_json

    config = load_quick_news_config()

    if not config.enabled:
        logger.info("新闻模块已禁用")
        return

    # 1. 拉取所有新闻源
    fetch_result = await fetch_all_sources()

    # 2. 扫描待分析新闻
    pending = _scan_pending_news()
    if not pending:
        logger.info("无待分析新闻")
        return

    logger.info(f"发现 {len(pending)} 条待分析新闻")

    # 3. 应用 limit
    if limit > 0:
        pending = pending[:limit]
        logger.info(f"应用 limit={limit}，处理前 {limit} 条")

    # 4. 逐个触发分析
    processed_count = 0
    start_time = time.monotonic()
    for news_data in pending:
        news_id = news_data["news_id"]
        title = news_data.get("title", "")
        summary = news_data.get("summary", "")
        content_path = _DEFAULT_DATA_DIR / "news" / news_id / "content.md"

        # 读取 content 作为 summary 的补充
        content = ""
        if content_path.exists():
            content = content_path.read_text(encoding="utf-8")

        # 用 summary || content 作为分析输入
        analysis_text = summary or content

        if not analysis_text or not analysis_text.strip():
            logger.warning(f"跳过无内容的新闻: {news_id} ({title})")
            continue

        logger.info(f"处理新闻: {title} ({news_id})")

        # 写入 pending 状态
        news_data["analysis_status"] = "pending"
        write_news_json(news_id, news_data)

        # 触发分析
        success, worth_deep = await submit_analysis(
            news_id=news_id,
            title=title,
            link=news_data.get("link", ""),
            summary=analysis_text,
        )

        # 更新状态
        news_data = read_news_json(news_id) or news_data
        if success:
            news_data["analysis_status"] = "done"
            # 从 analysis 中提取 worth_deep_analysis
            analysis = news_data.get("analysis", {})
            if isinstance(analysis, dict):
                news_data["worth_deep_analysis"] = analysis.get("worth_deep_analysis", False)
            write_news_json(news_id, news_data)
            processed_count += 1
            logger.info(f"分析完成: {news_id}, 值得深度分析: {news_data.get('worth_deep_analysis', False)}")
        else:
            news_data["analysis_status"] = "failed"
            write_news_json(news_id, news_data)
            logger.warning(f"分析失败: {news_id}")

    elapsed = time.monotonic() - start_time
    logger.info(f"新闻处理完成: {processed_count}/{len(pending)} 成功")

    # 5. 发送汇总通知
    if processed_count > 0:
        await _send_summary_notification(processed_count, elapsed)


async def _send_summary_notification(count: int, elapsed_seconds: float) -> None:
    """发送处理完成汇总通知。"""
    from .task_executor import get_gateway_client

    config = load_quick_news_config()
    recipients = config.delivery.recipients

    if not recipients:
        logger.info("无通知接收人，跳过汇总通知")
        return

    logger.info(f"准备发送汇总通知: {len(recipients)} 个接收人")

    mins = int(elapsed_seconds // 60)
    secs = int(elapsed_seconds % 60)
    elapsed_str = f"{mins}分{secs}秒" if mins > 0 else f"{secs}秒"
    message = f"📊 **新闻快速分析完成**\n\n处理了 {count} 条新闻\n总耗时: {elapsed_str}"

    client = await get_gateway_client()
    for recipient in recipients:
        try:
            result = await client.send_message(
                channel=recipient.channel,
                to=recipient.name,
                message=message,
                account_id=recipient.agent_id,
            )
            if result.get("ok"):
                logger.info(f"汇总通知已发送: {recipient.name}")
            else:
                logger.warning(f"汇总通知发送失败: {recipient.name}")
        except Exception as e:
            logger.error(f"汇总通知发送异常: {recipient.name} - {e}")


def setup_quick_news_jobs(scheduler: Scheduler) -> None:
    """注册新闻模块定时任务。"""
    from functools import partial

    config = load_quick_news_config()

    if not config.enabled:
        logger.info("新闻模块已禁用，跳过任务注册")
        return

    scheduler.add_interval_job(
        partial(fetch_all_quick_news, limit=0),
        job_id="news-fetch-all",
        minutes=config.interval_minutes,
    )

    logger.info(f"新闻任务已注册，间隔: {config.interval_minutes} 分钟")
