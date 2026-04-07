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
    1. cron.add（创建任务）
    2. cron.run（fire-and-forget 触发）
    3. 轮询 cron job state 等待完成（Gateway 管理，不依赖 Agent 写入）
    4. 从 session store 获取 session 信息
    5. cron.remove（删除任务）

    Args:
        message: 任务消息
        name: 任务名称（可选，默认自动生成时间戳名称）
        timeout_seconds: Agent 执行超时（秒），传给 cron payload
        session_poll_timeout_seconds: 轮询 job 完成状态的超时（秒）
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

        add_data = add_response.get("result", {}).get("details", {})
        cron_result.job_id = add_data.get("id", "")
        logger.info(f"任务创建成功: {cron_result.job_id}")

        # ========== 2. 触发任务（fire-and-forget）==========
        logger.info(f"触发任务: {cron_result.job_id}")

        async def _fire_and_forget_run():
            try:
                await client.call_tool(
                    "cron",
                    {"action": "run", "jobId": cron_result.job_id},
                    timeout=float(timeout_seconds + 60),
                )
            except Exception as e:
                logger.debug(f"cron.run 后台完成: {e}")

        asyncio.create_task(_fire_and_forget_run())

        # ========== 3. 轮询 job 完成状态（通过 cron.runs）==========
        run_ok = await _poll_job_completion(client, cron_result, session_poll_timeout_seconds)

        logger.info(f"任务运行完成: sessionId={cron_result.session_id}")

        # ========== 4. 删除任务 ==========
        await _remove_job(client, cron_result.job_id)

        if not run_ok:
            cron_result.error = f"任务在 {session_poll_timeout_seconds} 秒内未完成"
            return cron_result

        # 构造 context_path
        if cron_result.session_id:
            cron_result.context_path = str(get_openclaw_session_file(cron_result.agent_id, cron_result.session_id))
            session_file = Path(cron_result.context_path)
            cron_result.context_path_deleted = str(
                session_file.with_name(f"{session_file.stem}.deleted.*")
            )

        cron_result.success = True
        return cron_result

    except Exception as e:
        error_msg = f"任务执行异常: {e}"
        logger.error(error_msg, exc_info=True)
        cron_result.error = error_msg
        return cron_result


async def _poll_job_completion(
    client,
    cron_result: CronResult,
    timeout_seconds: int,
) -> bool:
    """轮询 cron.runs 等待任务完成。

    使用 cron.runs API 获取运行记录，从中提取完成状态和 session 信息。
    不依赖 Agent 写入任何文件，也不依赖 cron.list（已知可能返回空）。

    Returns:
        True 如果任务完成（ok 或 error），False 如果超时
    """
    logger.info(f"开始轮询任务完成状态: {cron_result.job_id}（超时 {timeout_seconds}s）")
    start = time.monotonic()

    # 等待 3 秒让任务启动
    await asyncio.sleep(3)

    while (time.monotonic() - start) < timeout_seconds:
        try:
            response = await client.call_tool(
                "cron",
                {"action": "runs", "jobId": cron_result.job_id},
                timeout=10.0,
            )

            if response.get("ok"):
                # cron.runs 返回格式: result.details.entries[]
                details = response.get("result", {}).get("details", {})
                entries = details.get("entries", [])

                if entries:
                    latest = entries[0]  # 最新的 run 记录
                    run_status = latest.get("status")
                    duration_ms = latest.get("durationMs", 0)
                    session_id = latest.get("sessionId")
                    session_key = latest.get("sessionKey")

                    if run_status in ("ok", "error"):
                        # 填充 session 信息
                        if session_id:
                            cron_result.session_id = session_id
                        if session_key:
                            cron_result.session_key = session_key
                            # 从 session_key 解析实际 agent_id
                            actual_agent = parse_agent_id_from_session_key(session_key)
                            if actual_agent:
                                cron_result.agent_id = actual_agent

                        if run_status == "ok":
                            logger.info(f"任务完成: ok（耗时 {duration_ms}ms）")
                            return True
                        else:
                            summary = latest.get("summary", "未知错误")
                            logger.warning(f"任务完成: error - {summary}")
                            cron_result.error = summary
                            return True

        except Exception as e:
            logger.debug(f"轮询异常（继续）: {e}")

        await asyncio.sleep(10)

    logger.error(f"任务轮询超时: {cron_result.job_id}")
    return False


def _extract_agent_from_session_key(session_key: str) -> str | None:
    """从 session key 提取 agent_id。

    session_key 格式: agent:{agent_id}:{label}:run:{session_id}
    """
    parts = session_key.split(":")
    if len(parts) >= 2 and parts[0] == "agent":
        return parts[1]
    return None


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
