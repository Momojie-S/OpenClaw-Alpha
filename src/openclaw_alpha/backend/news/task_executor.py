# -*- coding: utf-8 -*-
"""
新闻分析任务执行器

负责创建工作目录、加载任务模板、提交分析任务。
"""

import hashlib
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path

from openclaw_alpha.core.path_utils import (
    ensure_dir,
    get_news_analysis_task_dir,
    get_task_template_path,
)

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
    task_dir: str, title: str, link: str, content: str | None = None
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


def submit_analysis(
    title: str,
    link: str,
    summary: str,
) -> tuple[str | None, str | None]:
    """
    提交新闻分析任务

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
    # 1. 校验 summary
    if not summary or not summary.strip():
        raise ValueError(f"新闻内容不能为空: {title}")

    # 2. 创建任务目录
    date_str = datetime.now().strftime("%Y-%m-%d")
    news_id = generate_news_id(link)
    task_dir = get_news_analysis_task_dir(date_str, news_id)

    try:
        ensure_dir(task_dir)
        logger.info(f"创建任务目录: {task_dir}")
    except Exception as e:
        logger.error(f"创建任务目录失败: {e}")
        return (None, None)

    # 3. 构造任务消息（包含新闻内容，减少 agent 获取新闻的调用）
    try:
        message = build_message(str(task_dir), title, link, summary)
        logger.info(f"消息包含新闻内容（{len(summary)} 字符），agent 无需再获取")
    except FileNotFoundError as e:
        logger.error(f"加载任务模板失败: {e}")
        return (None, None)

    # 4. 构造命令
    cmd = [
        "openclaw",
        "cron",
        "add",
        "--name",
        f"news-analysis-{int(time.time())}",
        "--session",
        "isolated",
        "--message",
        message,
        "--at",
        "1m",
        "--delete-after-run",
        "--thinking",
        "low",
        "--timeout-seconds",
        "120",
        "--json",
    ]

    logger.info(f"提交分析任务: {title}")

    # 5. 执行命令
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            logger.error(f"添加任务失败: {result.stderr}")
            return (None, None)

        # 6. 解析返回
        data = json.loads(result.stdout)
        job_id = data["id"]
        logger.info(f"任务已创建: {job_id}, 任务目录: {task_dir}")
        return (job_id, str(task_dir))

    except json.JSONDecodeError as e:
        logger.error(f"解析返回结果失败: {e}\n输出: {result.stdout}")
        return (None, None)
    except Exception as e:
        logger.error(f"执行命令失败: {e}")
        return (None, None)
