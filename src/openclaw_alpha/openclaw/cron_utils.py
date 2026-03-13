# -*- coding: utf-8 -*-
"""
OpenClaw Cron 工具模块

提供 OpenClaw cron 相关的工具函数。

关联文档：
- docs/openclaw/cron.md
"""

import asyncio
import json
import logging
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .path_utils import get_openclaw_session_file, parse_agent_id_from_session_key

logger = logging.getLogger(__name__)


@dataclass
class CronResult:
    """
    OpenClaw cron add 返回结果

    Attributes:
        job_id: 任务 ID
        session_id: Session UUID
        session_key: Session Key（agent:{agent_id}:{session_label}）
        agent_id: Agent ID
        context_path: Session 上下文文件路径（.jsonl）
        context_path_deleted: Session 备份文件路径模式（.deleted.*），用于 session 被删除后回溯
        success: 是否成功
        error: 错误信息（如有）
    """

    job_id: str
    session_id: str | None
    session_key: str | None
    agent_id: str
    context_path: str | None
    context_path_deleted: str | None = None
    success: bool = True
    error: str | None = None


def parse_cron_result(data: dict[str, Any]) -> CronResult:
    """
    解析 openclaw cron add --expect-final 的返回结果

    Args:
        data: JSON 解析后的字典

    Returns:
        CronResult 对象

    Example:
        >>> result = parse_cron_result({
        ...     "id": "job-uuid",
        ...     "sessionId": "session-uuid",
        ...     "sessionKey": "agent:alpha:cron:job-uuid:run:session-uuid"
        ... })
        >>> result.job_id
        'job-uuid'
        >>> result.agent_id
        'alpha'
        >>> result.context_path
        '/home/user/.openclaw/agents/alpha/sessions/session-uuid.jsonl'
        >>> result.context_path_deleted
        '/home/user/.openclaw/agents/alpha/sessions/session-uuid.jsonl.deleted.*'
    """
    job_id = data.get("id", "")
    session_id = data.get("sessionId")
    session_key = data.get("sessionKey")

    # 解析 agent_id
    agent_id = "alpha"
    if session_key:
        agent_id = parse_agent_id_from_session_key(session_key)

    # 构造上下文路径
    context_path = None
    if session_id and agent_id:
        context_path = str(get_openclaw_session_file(agent_id, session_id))

    return CronResult(
        job_id=job_id,
        session_id=session_id,
        session_key=session_key,
        agent_id=agent_id,
        context_path=context_path,
    )


async def submit_cron_task(
    message: str,
    name: str | None = None,
    *,
    timeout_seconds: int = 300,
    session_poll_timeout_seconds: int = 300,
    delete_after_run: bool = True,
    thinking: str = "low",
    agent_id: str = "alpha",
    model: str | None = None,
    delivery_channel: str | None = None,
    delivery_to: str | None = None,
) -> CronResult:
    """
    提交 OpenClaw cron 任务（异步等待完成）

    流程：
    1. cron add --at "10m"（避免自动触发）
    2. cron run --expect-final（手动触发）
    3. 轮询 session store 获取 session 信息（使用 async 避免阻塞）
    4. cron rm（删除任务）

    Args:
        message: 任务消息
        name: 任务名称（可选，默认自动生成时间戳名称）
        timeout_seconds: 超时时间（秒），默认 300 秒（5 分钟）
        session_poll_timeout_seconds: 轮询 session store 的超时时间（秒），默认 300 秒（5 分钟）
        delete_after_run: 运行后删除任务，默认 True
        thinking: 思考级别，默认 "low"
        agent_id: Agent ID，默认 "alpha"
        model: 模型覆盖（如 "zai/glm-5"），None 则使用默认模型
        delivery_channel: 推送渠道（如 "wecom"），None 则不推送
        delivery_to: 推送目标（用户 ID 或聊天 ID）

    Returns:
        CronResult 对象，包含任务执行结果

    Example:
        >>> result = await submit_cron_task(
        ...     message="分析新闻：XXX",
        ...     name="news-analysis",
        ...     timeout_seconds=300,
        ...     session_poll_timeout_seconds=300,
        ...     model="zai/glm-5"
        ... )
        >>> if result.success:
        ...     print(f"任务完成: {result.job_id}")
        ...     print(f"上下文路径: {result.context_path}")
        ...     print(f"备份路径模式: {result.context_path_deleted}")
        ... else:
        ...     print(f"任务失败: {result.error}")
    """
    # 生成任务名称
    if not name:
        name = f"task-{int(time.time())}"

    # 生成 session key（确保正确路由到指定 agent）
    session_label = f"cron:{name}"
    session_key = f"agent:{agent_id}:{session_label}"

    # 构造 cron add 命令（使用 10m 避免自动触发）
    cmd = [
        "openclaw",
        "cron",
        "add",
        "--name",
        name,
        "--agent",
        agent_id,
        "--session",
        "isolated",
        "--session-key",
        session_key,
        "--message",
        message,
        "--at",
        "10m",  # 10分钟后执行，避免自动触发
        "--timeout-seconds",
        str(timeout_seconds),
        "--thinking",
        thinking,
        "--json",
    ]

    if model:
        cmd.extend(["--model", model])

    # 只有当 channel 和 to 都提供时才使用 announce 模式
    if delivery_channel and delivery_to:
        cmd.extend(["--announce", "--channel", delivery_channel, "--to", delivery_to])
    else:
        cmd.append("--no-deliver")

    logger.debug(f"执行 cron add: {' '.join(cmd[:5])}...")

    # 初始化 cron_result
    cron_result = CronResult(
        job_id="",
        session_id=None,
        session_key=None,
        agent_id=agent_id,
        context_path=None,
        success=False,
    )

    # 执行 cron add（使用 asyncio.to_thread 避免阻塞）
    try:
        result = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            error_msg = result.stderr.strip() or f"添加任务失败 (code: {result.returncode})"
            logger.error(f"添加任务失败: {error_msg}")
            cron_result.error = error_msg
            return cron_result

        # 解析返回结果
        data = json.loads(result.stdout)
        cron_result.job_id = data.get("id", "")
        cron_result.agent_id = agent_id

        logger.info(f"任务创建成功: {cron_result.job_id}")

    except json.JSONDecodeError as e:
        error_msg = f"解析返回结果失败: {e}"
        logger.error(error_msg)
        cron_result.error = error_msg
        return cron_result
    except Exception as e:
        error_msg = f"添加任务异常: {e}"
        logger.error(error_msg)
        cron_result.error = error_msg
        return cron_result

    # 手动触发任务（cron run --expect-final）
    logger.info(f"触发任务: {cron_result.job_id}")
    run_cmd = [
        "openclaw",
        "cron",
        "run",
        "--expect-final",
        "--timeout",
        str(timeout_seconds * 1000),  # 转换为毫秒
        cron_result.job_id,
    ]

    try:
        run_result = await asyncio.to_thread(subprocess.run, run_cmd, capture_output=True, text=True, check=False)

        if run_result.returncode != 0:
            error_msg = run_result.stderr.strip() or f"触发任务失败 (code: {run_result.returncode})"
            logger.error(f"触发任务失败: {error_msg}")
            # 删除任务
            await asyncio.to_thread(
                subprocess.run, ["openclaw", "cron", "rm", cron_result.job_id], capture_output=True
            )
            cron_result.error = error_msg
            return cron_result

        # 解析 run 返回结果（cron run 的输出不是 JSON）
        # 直接认为任务执行成功
        logger.info(f"任务运行完成")

    except json.JSONDecodeError as e:
        error_msg = f"解析 run 返回结果失败: {e}"
        logger.error(error_msg)
        # 删除任务
        await asyncio.to_thread(
            subprocess.run, ["openclaw", "cron", "rm", cron_result.job_id], capture_output=True
        )
        cron_result.error = error_msg
        return cron_result
    except Exception as e:
        error_msg = f"触发任务异常: {e}"
        logger.error(error_msg)
        # 删除任务
        await asyncio.to_thread(
            subprocess.run, ["openclaw", "cron", "rm", cron_result.job_id], capture_output=True
        )
        cron_result.error = error_msg
        return cron_result

    # 获取任务运行的 session 信息（异步轮询 session store）
    try:
        session_found = False
        for attempt in range(session_poll_timeout_seconds):
            await asyncio.sleep(1)  # 使用 async sleep 避免阻塞

            session_store_path = Path.home() / ".openclaw" / "agents" / agent_id / "sessions" / "sessions.json"

            if not session_store_path.exists():
                continue

            # 读取文件（同步读取，因为没有 async 版本）
            with open(session_store_path, encoding="utf-8") as f:
                sessions_data = json.load(f)

            # 查找包含 job_id 的 session
            for session_key, session_info in sessions_data.items():
                if cron_result.job_id in session_key and ":run:" in session_key:
                    cron_result.session_id = session_info.get("sessionId")
                    cron_result.session_key = session_key
                    # 构造 context_path 和 deleted 路径模式
                    cron_result.context_path = str(get_openclaw_session_file(agent_id, cron_result.session_id))
                    # deleted 文件路径模式：{stem}.deleted.*
                    session_file = Path(cron_result.context_path)
                    cron_result.context_path_deleted = str(session_file.with_name(f"{session_file.stem}.deleted.*"))
                    session_found = True
                    logger.info(f"获取运行信息: sessionId={cron_result.session_id}")
                    break

            if session_found:
                break

        if not session_found:
            logger.warning(
                f"未找到包含 job_id {cron_result.job_id} 的 session（轮询了 {session_poll_timeout_seconds} 秒）"
            )
            if session_store_path.exists():
                logger.debug(f"session store 中的 session keys: {list(sessions_data.keys())[:5]}")

    except Exception as e:
        logger.warning(f"获取运行信息失败: {e}")

    # 删除任务
    if delete_after_run:
        try:
            await asyncio.to_thread(
                subprocess.run, ["openclaw", "cron", "rm", cron_result.job_id], capture_output=True
            )
            logger.info(f"任务已删除: {cron_result.job_id}")
        except Exception as e:
            logger.warning(f"删除任务失败: {e}")

    # 标记成功
    cron_result.success = True
    logger.info(f"任务完成: {cron_result.job_id}, sessionId: {cron_result.session_id}")

    return cron_result
