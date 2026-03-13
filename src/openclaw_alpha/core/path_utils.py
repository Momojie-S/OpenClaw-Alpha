# -*- coding: utf-8 -*-
"""
路径工具模块

统一管理项目路径，避免到处硬编码路径。
"""

import os
from pathlib import Path


def get_project_root() -> Path:
    """
    获取项目根目录

    优先级：
    1. 环境变量 OPENCLAW_ALPHA_ROOT
    2. 从包路径推断（向上4级）

    Returns:
        项目根目录路径
    """
    # 优先使用环境变量
    env_root = os.getenv("OPENCLAW_ALPHA_ROOT")
    if env_root:
        return Path(env_root)

    # Fallback: 从当前文件推断
    # path_utils.py -> core -> openclaw_alpha -> src -> 项目根
    return Path(__file__).parent.parent.parent.parent


def get_config_dir() -> Path:
    """
    获取配置目录

    Returns:
        配置目录路径（~/.openclaw_alpha）
    """
    return Path.home() / ".openclaw_alpha"


def get_cache_dir() -> Path:
    """
    获取缓存目录

    Returns:
        缓存目录路径（~/.openclaw_alpha/cache）
    """
    return get_config_dir() / "cache"


def get_log_dir() -> Path:
    """
    获取日志目录

    Returns:
        日志目录路径（~/.openclaw_alpha/logs）
    """
    return get_config_dir() / "logs"


def get_skills_dir() -> Path:
    """
    获取 skills 目录

    Returns:
        skills 目录路径
    """
    return get_project_root() / "skills"


def get_workspace_dir() -> Path:
    """
    获取项目 workspace 目录

    workspace 是项目级的工作目录，用于存放各种任务的工作数据。

    Returns:
        workspace 目录路径（{project_root}/workspace/）
    """
    return get_project_root() / "workspace"


def get_task_template_path(skill_name: str, task_name: str) -> Path:
    """
    获取任务模板路径

    Args:
        skill_name: skill 名称（如 news_driven_investment）
        task_name: 任务名称（如 quick-news-analysis）

    Returns:
        任务模板文件路径
    """
    return get_skills_dir() / skill_name / "tasks" / f"{task_name}.md"


def get_news_analysis_task_dir(date: str, news_id: str) -> Path:
    """
    获取新闻分析任务目录

    Args:
        date: 日期（YYYY-MM-DD）
        news_id: 新闻 ID

    Returns:
        任务目录路径（{workspace_dir}/news_analysis/{date}/{news_id}）
    """
    return get_workspace_dir() / "news_analysis" / date / news_id


def ensure_dir(path: Path) -> Path:
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径

    Returns:
        目录路径
    """
    path.mkdir(parents=True, exist_ok=True)
    return path
