# -*- coding: utf-8 -*-
"""开发任务子模块 - 基于 OpenSpec"""

import asyncio
import json
import logging
import random
import subprocess
import time
from pathlib import Path

from openclaw_alpha.openclaw.cron_utils import submit_cron_task
from openclaw_alpha.openclaw.gateway_client import get_gateway_client

logger = logging.getLogger(__name__)

# Session 监控配置
SESSION_POLL_INTERVAL_SECONDS = 30  # 轮询间隔
SESSION_INACTIVE_THRESHOLD_SECONDS = 120  # Session 不活跃阈值（2分钟）

# OpenSpec 项目目录
OPENSPEC_PROJECT_DIR = Path(__file__).parent.parent.parent.parent.parent


def _run_openspec_list() -> list[str]:
    """
    调用 openspec list --json 获取活跃的 changes

    Returns:
        活跃 change 名称列表
    """
    try:
        result = subprocess.run(
            ["openspec", "list", "--json"],
            cwd=str(OPENSPEC_PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            logger.warning(f"openspec list 失败: {result.stderr}")
            return []

        data = json.loads(result.stdout)
        changes = data.get("changes", [])
        logger.debug(f"扫描到 {len(changes)} 个活跃 changes")
        return changes

    except FileNotFoundError:
        logger.error("openspec CLI 未安装")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"解析 openspec list 输出失败: {e}")
        return []
    except subprocess.TimeoutExpired:
        logger.error("openspec list 超时")
        return []
    except Exception as e:
        logger.error(f"运行 openspec list 异常: {e}")
        return []


def _check_change_completeness(change_name: str) -> bool:
    """
    检查 change 是否完整

    完整性标准：
    1. 有 proposal.md
    2. 有 design.md
    3. 有 specs/ 目录且至少一个 spec 文件
    4. 有 tasks.md 且包含未完成的 [ ] 任务

    Args:
        change_name: change 名称

    Returns:
        是否完整
    """
    change_dir = OPENSPEC_PROJECT_DIR / "openspec" / "changes" / change_name

    if not change_dir.exists():
        return False

    # 检查 proposal.md
    if not (change_dir / "proposal.md").exists():
        return False

    # 检查 design.md
    if not (change_dir / "design.md").exists():
        return False

    # 检查 specs/ 目录（至少一个 spec 文件）
    specs_dir = change_dir / "specs"
    if not specs_dir.exists():
        return False

    spec_files = list(specs_dir.rglob("*.md"))
    if not spec_files:
        return False

    # 检查 tasks.md 且包含未完成的 [ ] 任务
    tasks_file = change_dir / "tasks.md"
    if not tasks_file.exists():
        return False

    try:
        tasks_content = tasks_file.read_text(encoding="utf-8")
        # 检查是否有未完成的任务
        if "- [ ] " not in tasks_content:
            return False
    except Exception as e:
        logger.debug(f"读取 tasks.md 失败: {e}")
        return False

    return True


def _find_complete_changes() -> list[str]:
    """
    过滤出完整的 changes

    Returns:
        完整的 change 名称列表
    """
    active_changes = _run_openspec_list()

    complete_changes = []
    for change_name in active_changes:
        if _check_change_completeness(change_name):
            complete_changes.append(change_name)
            logger.debug(f"完整的 change: {change_name}")
        else:
            logger.debug(f"不完整的 change: {change_name}")

    return complete_changes


def _select_random_change(changes: list[str]) -> str | None:
    """
    随机选择一个 change

    Args:
        changes: change 名称列表

    Returns:
        选中的 change 名称，或 None
    """
    if not changes:
        return None

    selected = random.choice(changes)
    logger.info(f"随机选中 change: {selected}")
    return selected


def _build_message(change_name: str) -> str:
    """
    构造开发任务消息

    Args:
        change_name: change 名称

    Returns:
        消息内容
    """
    return f"使用 OpenSpec apply 流程完成 change {change_name}"


async def _check_session_status(session_id: str) -> dict:
    """
    检查 session 状态

    Returns:
        {
            "found": bool,
            "aborted": bool | None,
            "updated_at": int | None,  # 毫秒时间戳
            "inactive_seconds": float | None,
        }
    """
    try:
        client = await get_gateway_client()
        response = await client.list_sessions(active_minutes=60)

        if not response.get("ok"):
            logger.warning(f"获取 session 列表失败: {response.get('error')}")
            return {"found": False, "aborted": None, "updated_at": None, "inactive_seconds": None}

        sessions = response.get("result", {}).get("details", {}).get("sessions", [])
        now_ms = int(time.time() * 1000)

        for session in sessions:
            if session.get("sessionId") == session_id:
                updated_at = session.get("updatedAt")
                aborted = session.get("abortedLastRun")
                inactive_seconds = (now_ms - updated_at) / 1000 if updated_at else None

                return {
                    "found": True,
                    "aborted": aborted if aborted is not None else False,
                    "updated_at": updated_at,
                    "inactive_seconds": inactive_seconds,
                }

        # Session 不在列表中（可能已完成并清理）
        return {"found": False, "aborted": None, "updated_at": None, "inactive_seconds": None}

    except Exception as e:
        logger.error(f"检查 session 状态异常: {e}")
        return {"found": False, "aborted": None, "updated_at": None, "inactive_seconds": None}


async def _monitor_session(
    session_id: str,
    change_name: str,
    timeout_seconds: int,
) -> str:
    """
    监控 session 执行状态

    Args:
        session_id: Session ID
        change_name: change 名称
        timeout_seconds: 超时时间（秒）

    Returns:
        最终状态: "completed" | "aborted" | "timeout" | "error"
    """
    start_time = time.time()

    logger.info(f"开始监控 session: {session_id}, 超时: {timeout_seconds}s")

    while True:
        # 检查超时
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            logger.warning(f"Session 超时: {session_id}, 已运行 {elapsed:.0f}s")
            return "timeout"

        # 检查 change 是否已完成（tasks.md 全部 [x]）
        change_dir = OPENSPEC_PROJECT_DIR / "openspec" / "changes" / change_name
        tasks_file = change_dir / "tasks.md"

        if tasks_file.exists():
            try:
                tasks_content = tasks_file.read_text(encoding="utf-8")
                if "- [ ] " not in tasks_content:
                    logger.info(f"Change 任务已全部完成: {change_name}")
                    return "completed"
            except Exception as e:
                logger.debug(f"读取 tasks.md 失败: {e}")

        # 检查 session 状态
        status = await _check_session_status(session_id)

        if status["aborted"]:
            logger.warning(f"Session 被中止: {session_id}")
            return "aborted"

        # 如果 session 不在列表中
        if not status["found"]:
            # 等待一下再检查 tasks.md
            await asyncio.sleep(5)

            if tasks_file.exists():
                try:
                    tasks_content = tasks_file.read_text(encoding="utf-8")
                    if "- [ ] " not in tasks_content:
                        return "completed"
                except Exception:
                    pass

            # Session 消失但 tasks 未完成 = 异常
            logger.warning(f"Session 消失但 tasks 未完成: {session_id}")
            return "error"

        # 检查 session 是否长时间不活跃
        if status["inactive_seconds"] and status["inactive_seconds"] > SESSION_INACTIVE_THRESHOLD_SECONDS:
            logger.warning(f"Session 长时间不活跃: {status['inactive_seconds']:.0f}s")
            return "error"

        # 等待下次轮询
        await asyncio.sleep(SESSION_POLL_INTERVAL_SECONDS)


async def process(limit: int = 1, project_root: Path | None = None) -> bool:
    """
    处理开发任务

    Args:
        limit: 最多处理的任务数（目前只处理1个）
        project_root: 项目根目录（暂未使用）

    Returns:
        是否有任务被处理
    """
    # 查找完整的 changes
    complete_changes = _find_complete_changes()

    if not complete_changes:
        logger.debug("无完整的 OpenSpec changes")
        return False

    # 随机选择一个
    change_name = _select_random_change(complete_changes)
    if not change_name:
        return False

    logger.info(f"处理开发任务: {change_name}")

    # 构造消息
    message = _build_message(change_name)

    # 触发 Agent
    result = await submit_cron_task(
        message=message,
        name=f"dev-task-{change_name}",
        timeout_seconds=1800,  # 30分钟超时
        agent_id="alpha",
        thinking="low",
    )

    if not result.success:
        logger.error(f"开发任务提交失败: {result.error}")
        return False

    logger.info(f"开发任务已提交: {change_name}, sessionId: {result.session_id}")

    # 监控 session 执行
    if result.session_id:
        final_status = await _monitor_session(
            session_id=result.session_id,
            change_name=change_name,
            timeout_seconds=1800,
        )
        logger.info(f"Session 结束: {result.session_id}, 状态: {final_status}")

    return True
