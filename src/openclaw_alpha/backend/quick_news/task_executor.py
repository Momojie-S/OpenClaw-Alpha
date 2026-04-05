# -*- coding: utf-8 -*-
"""
新闻快速分析任务执行器

负责构造分析消息、提交 cron 任务、等待 Agent 完成。

关联文档：
- 设计文档：docs/design/news/quick-analysis.md
- v2 设计：docs/design/news/quick-analysis-v2.md
"""

import asyncio
import json
import logging
from pathlib import Path

from openclaw_alpha.core.path_utils import (
    ensure_dir,
    get_quick_news_analysis_task_dir,
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
    task_dir: str,
    news_id: str,
    title: str,
    link: str,
    summary: str,
) -> str:
    """构造分析任务消息。

    Args:
        task_dir: 任务工作目录
        news_id: 新闻 ID（CLI 层统一生成）
        title: 新闻标题
        link: 新闻链接
        summary: 新闻内容
    """
    template = load_task_template()

    message = f"""{template}

---

## 本次任务参数

- **任务目录**：{task_dir}
- **新闻 ID**：{news_id}
- **新闻标题**：{title}
- **新闻链接**：{link}
"""

    if summary:
        message += f"""
---

## 新闻内容

{summary}
"""

    return message


async def submit_analysis(
    news_id: str,
    title: str,
    link: str,
    summary: str,
) -> tuple[bool, bool]:
    """提交新闻快速分析任务（异步等待完成）。

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

    if not summary or not summary.strip():
        logger.warning(f"新闻内容为空: {news_id} ({title})")
        return (False, False)

    # 创建分析任务目录（用于 Agent 写 progress.md / report.md）
    date_str = datetime.now().strftime("%Y-%m-%d")
    task_dir = get_quick_news_analysis_task_dir(date_str, news_id)
    ensure_dir(task_dir)

    logger.info(f"提交快速分析任务: {title} ({news_id})")

    # 构造消息
    try:
        message = build_message(str(task_dir), news_id, title, link, summary)
    except FileNotFoundError as e:
        logger.error(f"加载任务模板失败: {e}")
        return (False, False)

    config = load_quick_news_config()

    # 提交 cron 任务
    cron_result = await submit_cron_task(
        message=message,
        name=f"news-analysis-{news_id}",
        delete_after_run=True,
        thinking="low",
        agent_id=config.agent_id,
        model=config.model,
        session_poll_timeout_seconds=config.cron.session_poll_timeout_seconds,
    )

    if not cron_result.success:
        logger.error(f"任务执行失败: {cron_result.error}")
        return (False, False)

    logger.info(f"任务已完成: {cron_result.job_id}, sessionId: {cron_result.session_id}")

    # Agent 通过 CLI update-news 将分析结果写入 news.json
    # Backend 等待 news.json 中出现 analysis 字段
    worth_deep_analysis = False
    analysis_found = False

    try:
        for _ in range(config.cron.report_wait_timeout_seconds):
            news_data = read_news_json(news_id)
            if news_data and "analysis" in news_data:
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
            logger.warning(f"分析结果未在 {config.cron.report_wait_timeout_seconds} 秒内出现: {news_id}")
    except Exception as e:
        logger.error(f"读取分析结果失败: {e}")

    # 推送分析结果给配置的 recipients
    if analysis_found:
        await _notify_recipients(
            news_id=news_id,
            title=title,
            task_dir=str(task_dir),
        )

    return (analysis_found, worth_deep_analysis)


async def _notify_recipients(
    news_id: str,
    title: str,
    task_dir: str,
) -> None:
    """推送分析结果通知。"""
    from openclaw_alpha.news.service import read_news_json

    config = load_quick_news_config()
    recipients = config.delivery.recipients

    if not recipients:
        return

    news_data = read_news_json(news_id) or {}
    analysis = news_data.get("analysis", {})
    worth_deep = analysis.get("worth_deep_analysis", False) if isinstance(analysis, dict) else False
    related_sectors = analysis.get("related_sectors", []) if isinstance(analysis, dict) else []
    related_companies = analysis.get("related_companies", []) if isinstance(analysis, dict) else []
    impact = analysis.get("impact_assessment", "") if isinstance(analysis, dict) else ""

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

    message = f"""📰 **{title}**

板块：{sectors_str or '无'}
公司：{companies_str or '无'}
影响：{impact[:100] + '...' if len(impact) > 100 else impact or '待分析'}
深度分析：{'✅ 建议深入' if worth_deep else '⏭️ 跳过'}

📂 任务目录：{task_dir}

---
💡 当前消息仅为通知，如需深入讨论，复制本消息后追加你想讨论的内容发送。"""

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
