# -*- coding: utf-8 -*-
"""开发任务子模块"""

import asyncio
import logging
import re
import time
from pathlib import Path

from openclaw_alpha.core.path_utils import get_workspace_dir
from openclaw_alpha.openclaw.cron_utils import submit_cron_task
from openclaw_alpha.openclaw.gateway_client import get_gateway_client

logger = logging.getLogger(__name__)

# 状态部分提取正则（只匹配 ## 状态 下的内容）
STATUS_SECTION_PATTERN = re.compile(
    r"##\s*状态\s*\n(.*?)(?=\n##|\Z)",
    re.DOTALL | re.IGNORECASE
)
# 完成状态的正则匹配（在状态部分内）
COMPLETED_PATTERN = re.compile(r"当前阶段[：:]\s*(完成|Phase\s*7)", re.IGNORECASE)
# 当前阶段提取
PHASE_PATTERN = re.compile(r"当前阶段[：:]\s*(.+?)(?:\n|$)", re.IGNORECASE)

# Session 监控配置
SESSION_POLL_INTERVAL_SECONDS = 30  # 轮询间隔
SESSION_INACTIVE_THRESHOLD_SECONDS = 120  # Session 不活跃阈值（2分钟）
PROGRESS_INACTIVE_THRESHOLD_SECONDS = 300  # progress.md 不更新阈值（5分钟）


def _scan_progress_files() -> list[Path]:
    """扫描进度文件目录"""
    progress_dir = get_workspace_dir().parent / "progress"

    if not progress_dir.exists():
        logger.debug(f"进度目录不存在: {progress_dir}")
        return []

    return list(progress_dir.glob("*.md"))


def _parse_progress_file(file_path: Path) -> dict:
    """
    解析进度文件

    只从"## 状态"部分提取信息，避免匹配文档其他位置的相同文本。

    Returns:
        {
            "path": Path,
            "current_phase": str,
            "is_completed": bool,
            "status_content": str,  # 状态部分的原始内容
        }
    """
    content = file_path.read_text(encoding="utf-8")

    # 提取状态部分
    status_match = STATUS_SECTION_PATTERN.search(content)
    if not status_match:
        logger.warning(f"进度文件缺少状态部分: {file_path.name}")
        return {
            "path": file_path,
            "current_phase": "未知",
            "is_completed": False,
            "status_content": "",
        }

    status_content = status_match.group(1)

    # 检查是否已完成（只在状态部分内匹配）
    is_completed = bool(COMPLETED_PATTERN.search(status_content))

    # 提取当前阶段（只在状态部分内匹配）
    phase_match = PHASE_PATTERN.search(status_content)
    current_phase = phase_match.group(1).strip() if phase_match else "未知"

    return {
        "path": file_path,
        "current_phase": current_phase,
        "is_completed": is_completed,
        "status_content": status_content,
    }


def _find_pending_task() -> dict | None:
    """
    找到一个待处理的开发任务

    Returns:
        进度文件信息，或 None
    """
    progress_files = _scan_progress_files()

    for file_path in progress_files:
        info = _parse_progress_file(file_path)
        if not info["is_completed"]:
            logger.info(f"发现待处理任务: {file_path.name}, 当前阶段: {info['current_phase']}")
            return info

    return None


def _build_message(progress_path: Path) -> str:
    """构造开发任务消息"""
    return f"""请按照开发任务流程（development-workflow）继续完成任务。

进度文件：{progress_path}

这是从上次进度继续。开始前请：
1. 重新阅读项目结构（project-overview.md）
2. 阅读相关设计文档
3. 读取进度文件了解当前状态
4. 继续执行待完成任务

完成后请更新进度文件。"""


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
    progress_path: Path,
    timeout_seconds: int,
) -> str:
    """
    监控 session 执行状态

    Args:
        session_id: Session ID
        progress_path: 进度文件路径
        timeout_seconds: 超时时间（秒）

    Returns:
        最终状态: "completed" | "aborted" | "timeout" | "error"
    """
    start_time = time.time()
    last_progress_mtime = 0

    logger.info(f"开始监控 session: {session_id}, 超时: {timeout_seconds}s")

    while True:
        # 检查超时
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            logger.warning(f"Session 超时: {session_id}, 已运行 {elapsed:.0f}s")
            return "timeout"

        # 检查 progress.md 完成状态
        if progress_path.exists():
            info = _parse_progress_file(progress_path)
            if info["is_completed"]:
                logger.info(f"Progress 标记完成: {progress_path.name}")
                return "completed"

            # 检查 progress.md 更新时间
            current_mtime = progress_path.stat().st_mtime
            if current_mtime > last_progress_mtime:
                last_progress_mtime = current_mtime
                logger.debug(f"Progress 已更新: {progress_path.name}")

        # 检查 session 状态
        status = await _check_session_status(session_id)

        if status["aborted"]:
            logger.warning(f"Session 被中止: {session_id}")
            return "aborted"

        # 如果 session 不在列表中，且 progress.md 已完成 = 正常完成
        if not status["found"]:
            # 等待一下再检查 progress.md（可能刚更新）
            await asyncio.sleep(5)
            if progress_path.exists():
                info = _parse_progress_file(progress_path)
                if info["is_completed"]:
                    return "completed"

            # Session 消失但 progress 未完成 = 异常
            logger.warning(f"Session 消失但 progress 未完成: {session_id}")
            return "error"

        # 检查 session 和 progress 是否都长时间不活跃
        if status["inactive_seconds"] and status["inactive_seconds"] > SESSION_INACTIVE_THRESHOLD_SECONDS:
            progress_inactive = time.time() - last_progress_mtime if last_progress_mtime > 0 else float("inf")

            if progress_inactive > PROGRESS_INACTIVE_THRESHOLD_SECONDS:
                logger.warning(
                    f"Session 和 progress 都不活跃: session_inactive={status['inactive_seconds']:.0f}s, "
                    f"progress_inactive={progress_inactive:.0f}s"
                )
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
    # 查找待处理任务
    task_info = _find_pending_task()

    if not task_info:
        logger.debug("无待处理开发任务")
        return False

    progress_path = task_info["path"]
    logger.info(f"处理开发任务: {progress_path.name}")

    # 构造消息
    message = _build_message(progress_path)

    # 触发 Agent（开发任务可能需要较长时间）
    result = await submit_cron_task(
        message=message,
        name=f"dev-task-{progress_path.stem}",
        timeout_seconds=1800,  # 30分钟超时
        agent_id="alpha",
        thinking="low",
    )

    if not result.success:
        logger.error(f"开发任务提交失败: {result.error}")
        return False

    logger.info(f"开发任务已提交: {progress_path.name}, sessionId: {result.session_id}")

    # 监控 session 执行
    if result.session_id:
        final_status = await _monitor_session(
            session_id=result.session_id,
            progress_path=progress_path,
            timeout_seconds=1800,
        )
        logger.info(f"Session 结束: {result.session_id}, 状态: {final_status}")

        # 如果异常结束，记录到进度文件
        if final_status in ("aborted", "timeout", "error"):
            _append_error_to_progress(progress_path, final_status)

    return True


def _append_error_to_progress(progress_path: Path, status: str) -> None:
    """将错误状态追加到进度文件"""
    try:
        status_text = {
            "aborted": "被中止",
            "timeout": "超时",
            "error": "异常停止",
        }.get(status, status)

        content = f"""

---

## 系统记录

**{time.strftime('%Y-%m-%d %H:%M:%S')}** - 任务{status_text}，需要人工检查。

"""
        with open(progress_path, "a", encoding="utf-8") as f:
            f.write(content)

    except Exception as e:
        logger.error(f"追加错误状态失败: {e}")
