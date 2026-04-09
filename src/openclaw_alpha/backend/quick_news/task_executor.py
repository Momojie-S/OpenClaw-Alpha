# -*- coding: utf-8 -*-
"""
新闻快速分析任务执行器 - 重构版

改进：
1. 统一异常捕获：整个 submit_analysis 用 try/except/finally 包裹
2. 失败时也发送通知
3. 返回明确的结果状态
"""

import asyncio
import json
import logging
from pathlib import Path

from openclaw_alpha.core.path_utils import (
    get_task_template_path,
)
from openclaw_alpha.openclaw.cron_utils import submit_cron_task
from openclaw_alpha.openclaw.gateway_client import get_gateway_client

logger = logging.getLogger(__name__)


def load_task_template() -> str:
    """加载新闻分析任务模板。"""
    template_path = get_task_template_path(
        skill_name="news_driven_investment",
        task_name="quick-news-analysis",
    )

    if not template_path.exists():
        raise FileNotFoundError(f"任务模板不存在: {template_path}")

    return template_path.read_text(encoding="utf-8")


def build_message(
    news_dir_relative: str,
    news_id: str,
    title: str,
    link: str,
    summary: str,
) -> str:
    """构造分析任务消息。

    Args:
        news_dir_relative: 新闻数据目录相对路径（如 data/news/{news_id}）
        news_id: 新闻 ID
        title: 新闻标题
        link: 新闻链接
        summary: 新闻内容
    """
    template = load_task_template()

    # 计算绝对路径（数据在项目根的 data/ 下，非 workspace/data/）
    from openclaw_alpha.core.path_utils import get_runtime_dir

    news_dir = get_runtime_dir() / news_dir_relative

    # 读取已有状态，让 Agent 知道哪些步骤可以跳过
    existing_status = []
    news_json_path = news_dir / "news.json"
    if news_json_path.exists():
        try:
            news_data = json.loads(news_json_path.read_text(encoding="utf-8"))
            if news_data.get("summary"):
                existing_status.append(f"summary 已存在: {news_data['summary']}")
            if news_data.get("analysis"):
                existing_status.append("analysis 已存在（如需更新请重写）")
        except Exception:
            pass

    status_note = ""
    if existing_status:
        status_note = "\n---\n\n## 已有数据状态\n\n" + "\n".join(f"- {s}" for s in existing_status) + "\n\n已有数据如准确可跳过对应步骤，优先完成缺失步骤。"

    message = f"""{template}

---

## 本次任务参数

- **NEWS_ID**: `{news_id}`
- **news_dir**: `{news_dir}`
- **TITLE**: {title}
- **LINK**: {link}{status_note}"""

    if summary:
        message += f"""

---

## 新闻内容

{summary}"""

    return message


async def submit_analysis(
    news_id: str,
    title: str,
    link: str,
    summary: str,
) -> tuple[bool, bool]:
    """
    提交新闻快速分析任务（异步等待完成）。

    改进：
    - 用 try/except/finally 包裹整个流程
    - 任何失败都发送通知
    - 返回明确的结果状态

    Args:
        news_id: 新闻 ID（CLI 层统一生成）
        title: 新闻标题
        link: 新闻链接
        summary: 新闻内容

    Returns:
        (success, worth_deep_analysis)
    """
    from datetime import datetime

    from openclaw_alpha.news.service import read_news_json, write_news_json

    # 初始化状态
    success = False
    worth_deep = False
    error_msg = None

    # 新闻数据目录（data/news/{news_id}/，相对于 runtime/）
    news_dir_relative = str(Path("data") / "news" / news_id)

    if not summary or not summary.strip():
        error_msg = "新闻内容为空"
        logger.warning(f"{error_msg}: {news_id} ({title})")
        await _send_result_notification(news_id, title, success=False, error=error_msg)
        return (False, False)

    try:
        logger.info(f"提交快速分析任务: {title} ({news_id})")

        config = load_quick_news_config()
        logger.info(f"  agent_id={config.agent_id}, model={config.model}")
        logger.info(f"  timeout={config.cron.agent_turn_timeout_seconds}s, session_poll_timeout={config.cron.session_poll_timeout_seconds}s")

        # 构造消息
        try:
            message = build_message(news_dir_relative, news_id, title, link, summary)
        except FileNotFoundError as e:
            error_msg = f"加载任务模板失败: {e}"
            logger.error(error_msg)
            await _send_result_notification(news_id, title, success=False, error=error_msg)
            return (False, False)

        # 提交 cron 任务
        cron_result = await submit_cron_task(
            message=message,
            name=f"news-analysis-{news_id}",
            timeout_seconds=config.cron.agent_turn_timeout_seconds,
            delete_after_run=True,
            thinking="low",
            agent_id=config.agent_id,
            model=config.model,
            session_poll_timeout_seconds=config.cron.session_poll_timeout_seconds,
        )

        if not cron_result.success:
            error_msg = cron_result.error or "任务执行失败（未知错误）"
            logger.error(f"任务执行失败: {error_msg}")
            await _send_result_notification(news_id, title, success=False, error=error_msg)
            return (False, False)

        logger.info(f"任务已完成: {cron_result.job_id}, sessionId: {cron_result.session_id}")

        # 轮询读取分析结果
        analysis_found = False

        try:
            # 短暂等待文件写入（Agent 可能刚完成 CLI 调用，文件 I/O 可能稍有延迟）
            for attempt in range(30):  # 最多等 30 秒
                news_data = read_news_json(news_id)
                if news_data and "analysis" in news_data:
                    logger.info(f"第 {attempt + 1} 次轮询: analysis 字段已写入")
                    analysis_found = True
                    analysis = news_data.get("analysis", {})
                    if isinstance(analysis, dict):
                        worth_deep_analysis = analysis.get("worth_deep_analysis", False)

                    # 追加 session 追溯信息
                    news_data["session"] = {
                        "job_id": cron_result.job_id,
                        "session_id": cron_result.session_id,
                        "context_path": cron_result.context_path,
                    }
                    write_news_json(news_id, news_data)
                    logger.info(f"已读取分析结果并追加 session 字段: {news_id}")
                    break
                await asyncio.sleep(1)
            else:
                error_msg = "任务完成但 analysis 字段未写入（轮询 30 次均未找到）"
                logger.warning(f"{error_msg}: {news_id}")
                await _send_result_notification(news_id, title, success=False, error=error_msg)
        except Exception as e:
            error_msg = f"读取分析结果失败: {e}"
            logger.error(error_msg)
            await _send_result_notification(news_id, title, success=False, error=error_msg)

        # 推送分析结果给配置的 recipients（仅成功时）
        if analysis_found:
            await _notify_recipients(
                news_id=news_id,
                title=title,
                news_dir=news_dir_relative,
            )

        success = analysis_found

    except Exception as e:
        # 捕获任何未预期的异常
        error_msg = f"submit_analysis 异常: {type(e).__name__}: {e}"
        logger.error(error_msg, exc_info=True)
        await _send_result_notification(news_id, title, success=False, error=error_msg)
        success = False

    finally:
        # 无论成功失败，都记录最终状态
        logger.info(f"submit_analysis 完成: news_id={news_id}, success={success}, worth_deep={worth_deep}, error={error_msg}")

    return (success, worth_deep)


async def _notify_recipients(
    news_id: str,
    title: str,
    news_dir: str,
) -> None:
    """
    推送分析结果通知（成功）。

    Args:
        news_id: 新闻 ID
        title: 新闻标题
        news_dir: 新闻数据目录相对路径
    """
    await _send_result_notification(news_id, title, success=True)


async def _send_result_notification(
    news_id: str,
    title: str,
    success: bool,
    error: str | None = None,
) -> None:
    """
    发送分析结果通知（成功或失败）。

    Args:
        news_id: 新闻 ID
        title: 新闻标题
        success: 成功或失败
        error: 错误信息（失败时）
    """
    from openclaw_alpha.news.service import read_news_json

    config = load_quick_news_config()
    recipients = config.delivery.recipients

    if not recipients:
        logger.info("无通知接收人，跳过通知")
        return

    news_data = read_news_json(news_id) or {}

    if success:
        # 成功通知（原有逻辑）
        analysis = news_data.get("analysis", {})
        worth_deep = analysis.get("worth_deep_analysis", False) if isinstance(analysis, dict) else False
        related_sectors = analysis.get("related_sectors", []) if isinstance(analysis, dict) else []
        related_companies = analysis.get("related_companies", []) if isinstance(analysis, dict) else []

        # 格式化相关公司
        companies_str = ""
        if related_companies:
            companies_list = [
                f"{c['name']}({c['code']})" if c.get("code") else c["name"]
                for c in related_companies[:5]
            ]
            companies_str = "、".join(companies_list)
            if len(related_companies) > 5:
                companies_str += f" 等{len(related_companies)}家"

        sectors_str = "、".join(related_sectors[:3])
        if len(related_sectors) > 3:
            sectors_str += f" 等{len(related_sectors)}个板块"

        summary_text = news_data.get("summary", "")
        summary_line = f"\n概括：{summary_text[:80] + '...' if len(summary_text) > 80 else summary_text}" if summary_text else ""

        message = f"""📰 **{title}**{summary_line}

板块：{sectors_str or '无'}
公司：{companies_str or '无'}
深度分析：{'✅ 建议深入' if worth_deep else '⏭️ 跳过'}

📂 News ID：{news_id}

---
💡 当前消息仅为通知，如需深入讨论，复制本消息后追加你想讨论的内容发送。"""
    else:
        # 失败通知
        error_msg = error or "未知错误"
        message = f"""❌ **新闻分析失败**

标题：{title}
News ID：{news_id}
错误：{error_msg}

请检查日志或手动重试。"""

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
                logger.info(f"已推送到 {recipient.channel}: {recipient.name}")
            else:
                logger.warning(f"推送失败: {recipient.name} - {result.get('error')}")
        except Exception as e:
            logger.error(f"推送异常: {recipient.name} - {e}")


def load_quick_news_config():
    """延迟导入避免循环依赖。"""
    from .config import load_quick_news_config
    return load_quick_news_config()
