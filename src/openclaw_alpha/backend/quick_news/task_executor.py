# -*- coding: utf-8 -*-
"""
新闻快速分析任务执行器

负责创建工作目录、加载任务模板、提交分析任务。

关联文档：
- 设计文档：docs/design/news/quick-analysis.md
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path

from openclaw_alpha.backend.quick_news.config import (
    extract_route_id,
    load_quick_news_config,
)
from openclaw_alpha.core.path_utils import (
    ensure_dir,
    get_news_archive_dir,
    get_quick_news_analysis_task_dir,
    get_task_template_path,
)
from openclaw_alpha.openclaw.cron_utils import submit_cron_task
from openclaw_alpha.openclaw.gateway_client import get_gateway_client

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
) -> tuple[str | None, Path | None, bool]:
    """
    提交新闻快速分析任务（异步等待完成）

    Args:
        title: 新闻标题
        link: 新闻链接
        summary: 新闻内容（必需，来自 RSS feed 的 summary 字段，将拼接到消息中减少 agent 获取新闻的调用）

    Returns:
        (job_id, task_dir, worth_deep_analysis) 成功时
        (None, None, False) 失败时

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
        return (None, None, False)

    try:
        message = build_message(str(task_dir), title, link, summary)
        logger.info(f"消息包含新闻内容（{len(summary)} 字符），agent 无需再获取")
    except FileNotFoundError as e:
        logger.error(f"加载任务模板失败: {e}")
        return (None, None, False)

    logger.info(f"提交快速分析任务: {title}")

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
        return (None, None, False)

    logger.info(f"任务已完成: {cron_result.job_id}, sessionId: {cron_result.session_id}, 任务目录: {task_dir}")

    # 等待 analysis.json 创建（新版设计要求输出结构化 JSON）
    analysis_json_path = Path(task_dir) / "analysis.json"
    worth_deep_analysis = False

    try:
        for i in range(config.cron.report_wait_timeout_seconds):
            if analysis_json_path.exists():
                # analysis.json 已创建，等待 1 秒确保写入完成
                await asyncio.sleep(1)

                # 读取并更新 analysis.json
                with open(analysis_json_path, 'r', encoding='utf-8') as f:
                    analysis = json.load(f)
                    worth_deep_analysis = analysis.get("worth_deep_analysis", False)

                # 追加 session 字段
                analysis["session"] = {
                    "job_id": cron_result.job_id,
                    "session_id": cron_result.session_id,
                    "context_path": cron_result.context_path,
                }

                # 写回 analysis.json
                with open(analysis_json_path, 'w', encoding='utf-8') as f:
                    json.dump(analysis, f, ensure_ascii=False, indent=2)

                logger.info(f"已读取分析结果并追加 session 字段: {analysis_json_path}")
                break
            await asyncio.sleep(1)
        else:
            logger.warning(
                f"analysis.json 未在 {config.cron.report_wait_timeout_seconds} 秒内创建"
            )
    except json.JSONDecodeError as e:
        logger.error(f"解析 analysis.json 失败: {e}")
    except Exception as e:
        logger.error(f"读取 analysis.json 失败: {e}")

    # 如果存在 report.md，追加系统运行信息（可选）
    report_path = Path(task_dir) / "report.md"
    if cron_result.session_key and cron_result.context_path and report_path.exists():
        try:
            # 等待 1 秒确保 report.md 写入完成
            await asyncio.sleep(1)
            append_system_info(
                str(task_dir), cron_result.job_id, cron_result.session_id,
                cron_result.context_path, cron_result.context_path_deleted
            )
            logger.info(f"已追加系统运行信息到 report.md")
        except Exception as e:
            logger.error(f"追加系统运行信息失败: {e}")

    # TODO: 触发深度分析
    # if worth_deep_analysis:
    #     trigger_deep_analysis(analysis, task_dir)

    # 保存新闻原文
    news_archive_path = _save_news_archive(title, link, summary, date_str)

    # 推送分析结果给多人
    await _notify_recipients(
        title=title,
        analysis_path=analysis_json_path,
        task_dir=str(task_dir),
        news_archive_path=news_archive_path,
    )

    return (cron_result.job_id, task_dir, worth_deep_analysis)


def _sanitize_filename(title: str) -> str:
    """
    清理新闻标题中的特殊字符，使其可作为文件名

    Args:
        title: 新闻标题

    Returns:
        安全的文件名
    """
    # 移除或替换不安全字符
    # 保留中英文、数字、空格、下划线、连字符
    safe = re.sub(r'[<>:"/\\|?*\n\r\t]', '', title)
    # 将多个空格压缩为一个
    safe = re.sub(r'\s+', ' ', safe).strip()
    # 限制长度（保留 50 字符，避免路径过长）
    if len(safe) > 50:
        safe = safe[:50]
    return safe or "untitled"


def _save_news_archive(
    title: str,
    link: str,
    content: str,
    date_str: str,
) -> Path | None:
    """
    保存新闻原文到存档目录

    Args:
        title: 新闻标题
        link: 新闻链接
        content: 新闻内容
        date_str: 日期字符串 (YYYY-MM-DD)

    Returns:
        存档文件路径，失败返回 None
    """
    try:
        route_id = extract_route_id(link)
        archive_dir = get_news_archive_dir(route_id, date_str)
        ensure_dir(archive_dir)

        # 清理标题作为文件名
        safe_title = _sanitize_filename(title)
        archive_path = archive_dir / f"{safe_title}.json"

        # 如果文件已存在，追加序号
        counter = 1
        while archive_path.exists():
            archive_path = archive_dir / f"{safe_title}_{counter}.json"
            counter += 1

        # 保存新闻数据
        news_data = {
            "title": title,
            "link": link,
            "content": content,
            "archived_at": datetime.now().isoformat(),
            "route_id": route_id,
        }

        with open(archive_path, 'w', encoding='utf-8') as f:
            json.dump(news_data, f, ensure_ascii=False, indent=2)

        logger.info(f"新闻原文已保存: {archive_path}")
        return archive_path

    except Exception as e:
        logger.error(f"保存新闻原文失败: {e}")
        return None


async def _notify_recipients(
    title: str,
    analysis_path: Path,
    task_dir: str,
    news_archive_path: Path | None,
) -> None:
    """
    推送分析结果给配置的 recipients

    使用 Gateway HTTP API 发送到企业微信

    Args:
        title: 新闻标题
        analysis_path: analysis.json 路径
        task_dir: 任务目录
        news_archive_path: 新闻原文存档路径
    """
    config = load_quick_news_config()
    recipients = config.delivery.recipients

    if not recipients:
        logger.debug("未配置 recipients，跳过推送")
        return

    # 读取 analysis.json
    analysis = {}
    if analysis_path.exists():
        try:
            with open(analysis_path, "r", encoding="utf-8") as f:
                analysis = json.load(f)
        except Exception as e:
            logger.warning(f"读取 analysis.json 失败: {e}")

    # 构造推送消息
    worth_deep = analysis.get("worth_deep_analysis", False)
    related_sectors = analysis.get("related_sectors", [])
    related_companies = analysis.get("related_companies", [])
    impact = analysis.get("impact_assessment", "")

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

    # 格式化板块
    sectors_str = "、".join(related_sectors[:3])
    if len(related_sectors) > 3:
        sectors_str += f" 等{len(related_sectors)}个板块"

    # 构造消息
    message = f"""📰 **{title}**

板块：{sectors_str or '无'}
公司：{companies_str or '无'}
影响：{impact[:100] + '...' if len(impact) > 100 else impact or '待分析'}
深度分析：{'✅ 建议深入' if worth_deep else '⏭️ 跳过'}

📂 任务目录：{task_dir}"""

    # 添加新闻原文路径
    if news_archive_path:
        message += f"""
📄 新闻原文：{news_archive_path}"""

    # 添加提示语
    message += """

---
💡 当前消息仅为通知，如需深入讨论，复制本消息后追加你想讨论的内容发送。"""

    # 推送给每个 recipient
    client = await get_gateway_client()
    for recipient in recipients:
        try:
            result = await client.send_message(
                channel="wecom",
                to=recipient,
                message=message,
            )
            if result.get("ok"):
                logger.info(f"已推送到企业微信: {recipient}")
            else:
                logger.warning(f"推送失败: {recipient} - {result.get('error')}")
        except Exception as e:
            logger.error(f"推送异常: {recipient} - {e}")
