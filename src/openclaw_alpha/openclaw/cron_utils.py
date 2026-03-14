# -*- coding: utf-8 -*-
"""
OpenClaw Cron 工具模块

提供 OpenClaw cron 相关的工具函数，使用 HTTP API 连接 Gateway。

关联文档：
- docs/openclaw/cron.md
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .gateway_client import get_gateway_client
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
    解析 cron.add 的返回结果

    Args:
        data: JSON 解析后的字典

    Returns:
        CronResult 对象
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
    提交 OpenClaw cron 任务（使用 HTTP API）

    流程：
    1. cron.add（设置 10m 后执行，避免自动触发）
    2. cron.run（手动触发）
    3. 轮询 session store 获取 session 信息
    4. cron.remove（删除任务）

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
    """
    # 生成任务名称
    if not name:
        name = f"task-{int(time.time())}"

    # 生成 session key（确保正确路由到指定 agent）
    session_label = f"cron:{name}"
    session_key = f"agent:{agent_id}:{session_label}"

    # 初始化结果
    cron_result = CronResult(
        job_id="",
        session_id=None,
        session_key=None,
        agent_id=agent_id,
        context_path=None,
        success=False,
    )

    try:
        # 获取 Gateway 客户端
        client = await get_gateway_client()

        # ========== 1. 添加任务 ==========
        # 计算触发时间：10 分钟后
        trigger_time = int((time.time() + 600) * 1000)

        add_params: dict[str, Any] = {
            "name": name,
            "agentId": agent_id,
            "sessionTarget": "isolated",
            "sessionKey": session_key,
            "schedule": {
                "kind": "at",
                "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(trigger_time / 1000)),
            },
            "payload": {
                "kind": "agentTurn",
                "message": message,
                "thinking": thinking,
                "timeoutSeconds": timeout_seconds,
            },
            "enabled": True,
        }

        if model:
            add_params["payload"]["model"] = model

        # 设置 delivery
        if delivery_channel and delivery_to:
            add_params["delivery"] = {
                "mode": "announce",
                "channel": delivery_channel,
                "to": delivery_to,
            }
        else:
            add_params["delivery"] = {"mode": "none"}

        logger.debug(f"cron.add 参数: {name}")
        add_response = await client.call_tool(
            "cron",
            {"action": "add", **add_params},
            timeout=30.0,
        )

        if not add_response.get("ok"):
            error = add_response.get("error", {})
            error_msg = error.get("message", "添加任务失败")
            logger.error(f"添加任务失败: {error_msg}")
            cron_result.error = error_msg
            return cron_result

        # HTTP API 返回格式: {"result": {"details": {...}}}
        add_data = add_response.get("result", {}).get("details", {})
        cron_result.job_id = add_data.get("id", "")
        logger.info(f"任务创建成功: {cron_result.job_id}")

        # ========== 2. 触发任务 ==========
        logger.info(f"触发任务: {cron_result.job_id}")
        run_response = await client.call_tool(
            "cron",
            {"action": "run", "jobId": cron_result.job_id},
            timeout=float(timeout_seconds),
        )

        if not run_response.get("ok"):
            error = run_response.get("error", {})
            error_msg = error.get("message", "触发任务失败")
            logger.error(f"触发任务失败: {error_msg}")
            # 尝试删除任务
            await _remove_job(client, cron_result.job_id)
            cron_result.error = error_msg
            return cron_result

        # 解析 run 结果
        run_data = run_response.get("result", {})
        cron_result.session_id = run_data.get("sessionId")
        cron_result.session_key = run_data.get("sessionKey")

        # 如果 run 没返回 session 信息，尝试从 session store 获取
        if not cron_result.session_id:
            await _poll_session_info(cron_result, agent_id, session_poll_timeout_seconds)

        # 构造 context_path
        if cron_result.session_id:
            cron_result.context_path = str(get_openclaw_session_file(agent_id, cron_result.session_id))
            session_file = Path(cron_result.context_path)
            cron_result.context_path_deleted = str(
                session_file.with_name(f"{session_file.stem}.deleted.*")
            )

        logger.info(f"任务运行完成: sessionId={cron_result.session_id}")

        # ========== 3. 删除任务 ==========
        if delete_after_run:
            await _remove_job(client, cron_result.job_id)

        cron_result.success = True
        return cron_result

    except Exception as e:
        error_msg = f"任务执行异常: {e}"
        logger.error(error_msg, exc_info=True)
        cron_result.error = error_msg
        return cron_result


async def _poll_session_info(
    cron_result: CronResult,
    agent_id: str,
    timeout_seconds: int,
) -> None:
    """轮询 session store 获取 session 信息"""
    try:
        for _ in range(timeout_seconds):
            await asyncio.sleep(1)

            session_store_path = (
                Path.home() / ".openclaw" / "agents" / agent_id / "sessions" / "sessions.json"
            )

            if not session_store_path.exists():
                continue

            with open(session_store_path, encoding="utf-8") as f:
                sessions_data = json.load(f)

            # 查找包含 job_id 的 session
            for session_key, session_info in sessions_data.items():
                if cron_result.job_id in session_key and ":run:" in session_key:
                    cron_result.session_id = session_info.get("sessionId")
                    cron_result.session_key = session_key
                    logger.info(f"获取运行信息: sessionId={cron_result.session_id}")
                    return

        logger.warning(
            f"未找到包含 job_id {cron_result.job_id} 的 session（轮询了 {timeout_seconds} 秒）"
        )

    except Exception as e:
        logger.warning(f"获取运行信息失败: {e}")


async def _remove_job(client, job_id: str) -> None:
    """删除任务"""
    try:
        response = await client.call_tool(
            "cron",
            {"action": "remove", "jobId": job_id},
            timeout=10.0,
        )
        if response.get("ok"):
            logger.info(f"任务已删除: {job_id}")
        else:
            logger.warning(f"删除任务失败: {response.get('error', {}).get('message', '未知错误')}")
    except Exception as e:
        logger.warning(f"删除任务异常: {e}")
