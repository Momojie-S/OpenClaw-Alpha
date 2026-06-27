# -*- coding: utf-8 -*-
"""新闻快速分析模块定时任务

Backend 通过 CLI service 层拉取新闻，用 news.json 的 analysis_status 追踪分析状态。
"""

import asyncio
import json
import logging
import time
from pathlib import Path

from ...core.path_utils import get_runtime_dir, get_task_template_path
from ..scheduler import Scheduler
from .config import QuickNewsConfig, load_quick_news_config
from .event_review_config import load_event_review_config
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
        if status in (None, "pending", "failed"):
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
        success, _worth_deep = await submit_analysis(
            news_id=news_id,
            title=title,
            link=news_data.get("link", ""),
            summary=analysis_text,
        )

        # 更新状态
        news_data = read_news_json(news_id) or news_data
        if success:
            news_data["analysis_status"] = "done"
            write_news_json(news_id, news_data)
            processed_count += 1
            analysis = news_data.get("analysis", {})
            logger.info(f"分析完成: {news_id}, 值得深度分析: {analysis.get('worth_deep_analysis', False) if isinstance(analysis, dict) else False}")
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


async def _send_deep_analysis_notification(event_id: str, title: str) -> None:
    """发送深度分析完成通知。"""
    from .task_executor import get_gateway_client

    config = load_quick_news_config()
    recipients = config.delivery.recipients

    if not recipients:
        logger.info("无通知接收人，跳过深度分析通知")
        return

    logger.info(f"准备发送深度分析通知: {event_id} ({title})")

    message = f"📰 **深度分析完成**\n\n事件: {title}"

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
                logger.info(f"深度分析通知已发送: {recipient.name}")
            else:
                logger.warning(f"深度分析通知发送失败: {recipient.name}")
        except Exception as e:
            logger.error(f"深度分析通知发送异常: {recipient.name} - {e}")


async def review_all_ongoing_events() -> dict:
    """扫描所有 ongoing 事件，逐个触发回顾任务。"""
    from openclaw_alpha.news.service import list_events as svc_list_events
    from .task_executor import submit_event_review

    review_config = load_event_review_config()

    if not review_config.enabled:
        logger.info("事件回顾已禁用")
        return {"reviewed": 0, "skipped": 0}

    result = svc_list_events(status="ongoing", limit=1000)
    events = result.get("events", [])

    if not events:
        logger.info("无 ongoing 事件需要回顾")
        return {"reviewed": 0, "skipped": 0}

    logger.info(f"发现 {len(events)} 个 ongoing 事件待回顾")

    reviewed = 0
    skipped = 0
    for event in events:
        event_id = event.get("event_id")
        if not event_id:
            skipped += 1
            continue

        try:
            success = await submit_event_review(
                event_id=event_id,
                agent_id=review_config.agent_id,
                model=review_config.model,
            )
            if success:
                reviewed += 1
                logger.info(f"事件回顾完成: {event_id}")
            else:
                skipped += 1
                logger.warning(f"事件回顾失败: {event_id}")
        except Exception as e:
            skipped += 1
            logger.error(f"事件回顾异常: {event_id} - {e}")

    logger.info(f"事件回顾完成: reviewed={reviewed}, skipped={skipped}")
    return {"reviewed": reviewed, "skipped": skipped}


def _scan_deep_analysis_events() -> list[dict]:
    """扫描需要深度分析的事件。

    条件：status=ongoing AND needs_deep_analysis=true
          AND len(news_ids) > (deep_analysis?.analyzed_news_count ?? 0)
    """
    from openclaw_alpha.news.service import list_events as svc_list_events

    result = svc_list_events(status="ongoing", needs_deep=True, limit=1000)
    events = result.get("events", [])

    # 进一步过滤：有新新闻未分析
    matched = []
    for event in events:
        news_ids = event.get("news_ids", [])
        deep = event.get("deep_analysis")
        analyzed_count = deep.get("analyzed_news_count", 0) if deep else 0
        if len(news_ids) > analyzed_count:
            matched.append(event)

    return matched


async def execute_deep_analysis() -> None:
    """深度分析入口函数：扫描需深入的事件，逐个触发 Agent。"""
    from openclaw_alpha.news.service import read_news_json
    from .task_executor import submit_deep_analysis

    events = _scan_deep_analysis_events()
    if not events:
        logger.info("无需深度分析的事件")
        return

    logger.info(f"发现 {len(events)} 个事件需要深度分析")

    for event in events:
        event_id = event["event_id"]
        title = event.get("title", "")
        news_ids = event.get("news_ids", [])

        # 收集关联新闻信息
        news_list = []
        for n in news_ids:
            nid = n.get("news_id") if isinstance(n, dict) else n
            news_data = read_news_json(nid)
            if news_data:
                news_list.append(news_data)

        # 触发深度分析
        event_dir = str((_DEFAULT_DATA_DIR / "events" / event_id).resolve())
        try:
            success = await submit_deep_analysis(
                event_id=event_id,
                event_dir=event_dir,
                title=title,
                news_list=news_list,
            )
        except Exception as e:
            logger.error(f"深度分析提交异常: {event_id} - {e}")
            continue

        if success:
            # 更新 event.json
            from openclaw_alpha.news.service import get_event
            from openclaw_alpha.core.path_utils import get_runtime_dir

            event_path = get_runtime_dir() / "data" / "events" / event_id / "event.json"
            import json as _json
            event_data = _json.loads(event_path.read_text(encoding="utf-8"))
            event_data["needs_deep_analysis"] = False
            event_data["deep_analysis"] = {
                "analyzed_news_count": len(news_ids),
                "analyzed_at": _now_iso(),
            }
            event_path.write_text(_json.dumps(event_data, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info(f"深度分析完成: {event_id}")
            # 发送深度分析完成通知
            await _send_deep_analysis_notification(event_id, title)
        else:
            logger.warning(f"深度分析失败: {event_id}")


def _now_iso() -> str:
    """当前时间 ISO 8601（东八区）。"""
    from datetime import datetime, timezone, timedelta
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).isoformat()


def register_quick_news_tasks(registry: 'TaskRegistry', scheduler: Scheduler) -> None:
    """注册新闻模块任务到队列和调度器。"""
    from ..task_queue import TaskRegistry as TR

    config = load_quick_news_config()

    if not config.enabled:
        logger.info("新闻模块已禁用，跳过任务注册")
        return

    # 注册任务类型到 registry
    async def news_fetch_entry():
        await fetch_all_quick_news(limit=config.fetch_limit)

    registry.register("news_fetch", news_fetch_entry, priority=2)

    # 注册深度分析任务
    async def deep_analysis_entry():
        await execute_deep_analysis()

    registry.register("deep_analysis", deep_analysis_entry, priority=3)

    # 注册事件回顾任务
    review_config = load_event_review_config()
    if review_config.enabled:
        async def event_review_entry():
            await review_all_ongoing_events()

        registry.register("event_review", event_review_entry, priority=1)

        scheduler.add_daily_job(
            lambda: asyncio.create_task(_enqueue_safe("event_review")),
            job_id="trigger-event-review",
            time_str=review_config.schedule_time,
        )
        logger.info(f"事件回顾任务已注册，每日 {review_config.schedule_time}")

    # 注册调度触发
    scheduler.add_interval_job(
        lambda: asyncio.create_task(_enqueue_safe("news_fetch")),
        job_id="trigger-news-fetch",
        minutes=config.interval_minutes,
    )

    # 深度分析调度触发
    scheduler.add_interval_job(
        lambda: asyncio.create_task(_enqueue_safe("deep_analysis")),
        job_id="trigger-deep-analysis",
        minutes=config.deep_analysis_interval_minutes,
    )
    logger.info(f"深度分析任务已注册，间隔: {config.deep_analysis_interval_minutes} 分钟")

    logger.info(f"新闻任务已注册，间隔: {config.interval_minutes} 分钟")


async def _enqueue_safe(task_type: str) -> None:
    """安全入队，避免未初始化时报错。"""
    from ..task_queue import _global_queue
    if _global_queue:
        await _global_queue.enqueue(task_type)
