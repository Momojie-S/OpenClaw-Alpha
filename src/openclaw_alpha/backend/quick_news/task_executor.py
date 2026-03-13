# -*- coding: utf-8 -*-
"""
新闻分析任务执行器

负责创建工作目录、加载任务模板、提交分析任务。

关联文档：
- 设计文档：docs/architecture/news-subscription.md
"""

import asyncio
import hashlib
import logging
import time
from datetime import datetime
from pathlib import Path

from openclaw_alpha.backend.quick_news.config import load_news_config
from openclaw_alpha.core.path_utils import (
    ensure_dir,
    get_quick_news_analysis_task_dir,
    get_task_template_path,
)
from openclaw_alpha.openclaw.cron_utils import submit_cron_task

logger = logging.getLogger(__name__)


def load_task_template() -> str:
    """
    加载新闻分析任务模板

    Returns:
        任务模板内容

    Raises:
        FileNotFoundError: 模板文件不存在
    """
    template_path = get_task_template_path(
        skill_name="news_driven_investment",
        task_name="quick-news-analysis",
    )

    if not template_path.exists():
        raise FileNotFoundError(f"任务模板不存在: {template_path}")

    return template_path.read_text(encoding="utf-8")


def build_message(
    task_dir: str,
    title: str,
    link: str,
    content: str | None = None,
) -> str:
    """
    构造分析任务消息

    Args:
        task_dir: 任务工作目录
        title: 新闻标题
        link: 新闻链接
        content: 新闻内容（可选，如提供将拼接到消息中）

    Returns:
        完整的任务消息（模板 + 参数 + 内容）
    """
    template = load_task_template()

    # 任务参数（在消息中提供，减少 md 文件内容）
    message = f"""{template}

---

## 本次任务参数

- **任务目录**：{task_dir}
- **新闻标题**：{title}
- **新闻链接**：{link}
"""

    # 添加新闻内容（如果有）
    if content:
        message += f"""
---

## 新闻内容

{content}
"""

    return message


def generate_news_id(link: str) -> str:
    """
    根据链接生成新闻 ID

    Args:
        link: 新闻链接

    Returns:
        8位新闻 ID
    """
    return hashlib.md5(link.encode()).hexdigest()[:8]


async def submit_analysis(
    title: str,
    link: str,
    summary: str,
) -> tuple[str | None, Path | None]:
    """
    提交新闻分析任务（异步等待完成）

    Args:
        title: 新闻标题
        link: 新闻链接
        summary: 新闻内容（必需，来自 RSS feed 的 summary 字段，将拼接到消息中减少 agent 获取新闻的调用）

    Returns:
        (job_id, workspace_dir) 成功时
        (None, None) 失败时

    Raises:
        ValueError: summary 为空时
    """
    from openclaw_alpha.skills.news_driven_investment.news_helper import append_system_info

    if not summary or not summary.strip():
        raise ValueError(f"新闻内容不能为空: {title}")

    date_str = datetime.now().strftime("%Y-%m-%d")
    news_id = generate_news_id(link)
    task_dir = get_quick_news_analysis_task_dir(date_str, news_id)

    try:
        ensure_dir(task_dir)
        logger.info(f"创建任务目录: {task_dir}")
    except Exception as e:
        logger.error(f"创建任务目录失败: {e}")
        return (None, None)

    try:
        message = build_message(str(task_dir), title, link, summary)
        logger.info(f"消息包含新闻内容（{len(summary)} 字符），agent 无需再获取")
    except FileNotFoundError as e:
        logger.error(f"加载任务模板失败: {e}")
        return (None, None)

    logger.info(f"提交分析任务: {title}")

    config = load_quick_news_config()

    cron_result = await submit_cron_task(
        message=message,
        name=f"news-analysis-{news_id}",
        delete_after_run=True,
        thinking="low",
        agent_id=config.agent_id,
        model=config.model,
        delivery_channel=config.delivery.channel,
        delivery_to=config.delivery.to,
        session_poll_timeout_seconds=config.cron.session_poll_timeout_seconds,
    )

    if not cron_result.success:
        logger.error(f"任务执行失败: {cron_result.error}")
        return (None, None)

    logger.info(f"任务已完成: {cron_result.job_id}, sessionId: {cron_result.session_id}, 任务目录: {task_dir}")

    # 等待 report.md 创建（使用 async 避免阻塞）
    report_path = Path(task_dir) / "report.md"
    if cron_result.session_key and cron_result.context_path:
        try:
            for i in range(config.cron.report_wait_timeout_seconds):
                if report_path.exists():
                    # report.md 已创建，等待 2 秒确保写入完成
                    await asyncio.sleep(2)
                    append_system_info(
                        str(task_dir), cron_result.job_id, cron_result.session_id, cron_result.context_path, cron_result.context_path_deleted
                    )
                    logger.info(f"已追加系统运行信息: {report_path}")
                    break
                await asyncio.sleep(1)
            else:
                logger.warning(
                    f"report.md 未在 {config.cron.report_wait_timeout_seconds} 秒内创建，跳过追加系统信息"
                )
        except FileNotFoundError as e:
            logger.warning(f"报告文件不存在，跳过追加: {e}")
        except Exception as e:
            logger.error(f"追加系统运行信息失败: {e}")

    return (cron_result.job_id, task_dir)
