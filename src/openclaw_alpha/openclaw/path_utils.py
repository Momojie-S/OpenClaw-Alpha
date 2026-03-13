# -*- coding: utf-8 -*-
"""
OpenClaw 路径工具模块

提供 OpenClaw 框架相关的路径工具函数。

关联文档：
- docs/openclaw/cron.md
"""

from pathlib import Path


def get_openclaw_home() -> Path:
    """
    获取 OpenClaw 主目录

    Returns:
        OpenClaw 主目录路径（~/.openclaw）
    """
    return Path.home() / ".openclaw"


def get_openclaw_agents_dir() -> Path:
    """
    获取 OpenClaw agents 目录

    Returns:
        agents 目录路径（~/.openclaw/agents）
    """
    return get_openclaw_home() / "agents"


def get_openclaw_agent_dir(agent_id: str) -> Path:
    """
    获取指定 agent 的目录

    Args:
        agent_id: Agent ID（如 "alpha", "main"）

    Returns:
        agent 目录路径（~/.openclaw/agents/{agent_id}）
    """
    return get_openclaw_agents_dir() / agent_id


def get_openclaw_sessions_dir(agent_id: str) -> Path:
    """
    获取指定 agent 的 sessions 目录

    Args:
        agent_id: Agent ID（如 "alpha", "main"）

    Returns:
        sessions 目录路径（~/.openclaw/agents/{agent_id}/sessions）
    """
    return get_openclaw_agent_dir(agent_id) / "sessions"


def get_openclaw_session_file(agent_id: str, session_id: str) -> Path:
    """
    获取 OpenClaw session 上下文存储文件路径

    Args:
        agent_id: Agent ID（如 "alpha", "main"）
        session_id: Session UUID

    Returns:
        session 文件路径（~/.openclaw/agents/{agent_id}/sessions/{session_id}.jsonl）

    Example:
        >>> get_openclaw_session_file("alpha", "fab6e5fa-d029-4c68-9aa2-28eed6497ab2")
        PosixPath('/home/user/.openclaw/agents/alpha/sessions/fab6e5fa-d029-4c68-9aa2-28eed6497ab2.jsonl')
    """
    return get_openclaw_sessions_dir(agent_id) / f"{session_id}.jsonl"


def parse_agent_id_from_session_key(session_key: str) -> str:
    """
    从 sessionKey 中解析 agent_id

    Args:
        session_key: Session Key（格式：agent:{agent_id}:{session_label}）

    Returns:
        agent_id

    Example:
        >>> parse_agent_id_from_session_key("agent:alpha:direct:momojie")
        'alpha'
        >>> parse_agent_id_from_session_key("agent:main:cron:job-123")
        'main'
    """
    parts = session_key.split(":")
    if len(parts) >= 2 and parts[0] == "agent":
        return parts[1]
    return "alpha"  # 默认返回 alpha
