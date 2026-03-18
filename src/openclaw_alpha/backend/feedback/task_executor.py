# -*- coding: utf-8 -*-
"""
用户反馈处理任务执行器

负责创建工作目录、加载任务模板、提交分析任务。

关联文档：
- 设计文档：docs/design/feedback/overview.md
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from openclaw_alpha.backend.feedback.config import load_feedback_config
from openclaw_alpha.openclaw.cron_utils import submit_cron_task
from openclaw_alpha.openclaw.gateway_client import get_gateway_client

logger = logging.getLogger(__name__)


def get_feedback_dir(project_root: Path | None = None, subdir: str = "new") -> Path:
    """
    获取反馈目录

    Args:
        project_root: 项目根目录
        subdir: 子目录名（new 或 done）
    """
    if project_root is None:
        project_root = Path(__file__).parent.parent.parent.parent.parent
    return project_root / "workspace" / "feedback" / subdir


def get_feedback_task_dir(project_root: Path | None = None, date: str | None = None, feedback_id: str = "") -> Path:
    """
    获取反馈任务目录

    Args:
        project_root: 项目根目录
        date: 日期字符串（YYYY-MM-DD），None 则使用今天
        feedback_id: 反馈 ID

    Returns:
        任务目录路径
    """
    if project_root is None:
        project_root = Path(__file__).parent.parent.parent.parent.parent

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    return (
        project_root
        / "workspace"
        / "feedback"
        / "tasks"
        / date
        / feedback_id
    )


def load_workflow_template() -> str:
    """
    加载反馈处理任务模板

    Returns:
        任务模板内容
    """
    project_root = Path(__file__).parent.parent.parent.parent.parent
    template_path = (
        project_root
        / "docs"
        / "workflow"
        / "feedback-workflow.md"
    )

    if not template_path.exists():
        raise FileNotFoundError(f"任务模板不存在: {template_path}")

    return template_path.read_text(encoding="utf-8")


def build_message(
    task_dir: str,
    json_path: str,
    feedback_content: str,
) -> str:
    """
    构造反馈处理任务消息

    Args:
        task_dir: 任务工作目录
        json_path: 反馈 JSON 文件路径
        feedback_content: 反馈内容

    Returns:
        完整的任务消息（模板 + 参数）
    """
    template = load_workflow_template()

    message = f"""{template}

---

## 本次任务参数

- **任务目录**：{task_dir}
- **反馈 JSON**：{json_path}

---

## 反馈内容

{feedback_content}
"""

    return message


def update_feedback_status(
    feedback_path: Path,
    status: str,
    **fields,
) -> bool:
    """
    更新反馈状态

    Args:
        feedback_path: 反馈 JSON 文件路径
        status: 新状态
        **fields: 其他要更新的字段

    Returns:
        是否成功
    """
    try:
        with open(feedback_path, "r", encoding="utf-8") as f:
            feedback = json.load(f)

        feedback["status"] = status

        # 更新其他字段
        for key, value in fields.items():
            feedback[key] = value

        # 原子写入
        temp_path = feedback_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(feedback, f, ensure_ascii=False, indent=2)
        temp_path.replace(feedback_path)

        return True

    except Exception as e:
        logger.error(f"更新反馈状态失败: {e}")
        return False


async def submit_feedback_task(
    feedback_path: Path,
    feedback: dict,
) -> bool:
    """
    提交反馈处理任务

    Args:
        feedback_path: 反馈 JSON 文件路径
        feedback: 反馈数据

    Returns:
        是否成功
    """
    config = load_feedback_config()
    feedback_id = feedback["id"]
    content = feedback["content"]

    # 创建任务目录
    task_dir = get_feedback_task_dir(feedback_id=feedback_id)
    task_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"创建任务目录: {task_dir}")

    # 创建 progress.md
    progress_path = task_dir / "progress.md"
    source_user = feedback.get("source_user", "未指定")
    source_channel = feedback.get("source_channel", "未指定")
    background = feedback.get("background", "")

    progress_content = f"""# 用户反馈处理

- **反馈 ID**：{feedback_id}
- **反馈时间**：{feedback['submitted_at']}
- **提交用户**：{source_user}
- **提交渠道**：{source_channel}
{f'- **背景简述**：{background}' if background else ''}
## 处理进度

- [ ] 开始处理
"""

    with open(progress_path, "w", encoding="utf-8") as f:
        f.write(progress_content)

    # 记录用户信息（可能为空）
    source_user = feedback.get("source_user", "未指定")
    source_channel = feedback.get("source_channel", "未指定")
    logger.info(f"提交反馈处理任务: {feedback_id} (用户: {source_user}, 渠道: {source_channel})")

    try:
        # 构造任务消息
        message = build_message(str(task_dir), str(feedback_path), content)

        # 提交 Cron 任务
        cron_result = await submit_cron_task(
            message=message,
            name=f"feedback-{feedback_id}",
            timeout_seconds=300,
            session_poll_timeout_seconds=config.cron.session_poll_timeout_seconds,
            delete_after_run=False,  # 不自动删除，等待处理完成
            thinking="low",
            agent_id=config.agent_id,
            model=config.model,
        )

        if not cron_result.success:
            logger.error(f"任务执行失败: {cron_result.error}")
            # 重置为 pending
            update_feedback_status(feedback_path, "pending")
            return False

        # 更新反馈状态为 processing
        update_feedback_status(
            feedback_path,
            "processing",
            task_dir=str(task_dir),
            job_id=cron_result.job_id,
            session_id=cron_result.session_id,
            context_path=cron_result.context_path,
            context_path_deleted=cron_result.context_path_deleted,
            started_at=datetime.now().isoformat(),
        )

        logger.info(
            f"任务已提交: {cron_result.job_id}, sessionId: {cron_result.session_id}"
        )

        # 等待处理完成（轮询 decision 字段）
        await _wait_for_completion(
            feedback_path,
            config.cron.result_wait_timeout_seconds,
        )

        return True

    except Exception as e:
        logger.error(f"提交反馈任务异常: {e}", exc_info=True)
        # 重置为 pending
        update_feedback_status(feedback_path, "pending")
        return False


async def _wait_for_completion(
    feedback_path: Path,
    timeout_seconds: int,
) -> None:
    """
    等待反馈处理完成（轮询 decision 字段）

    Args:
        feedback_path: 反馈 JSON 文件路径
        timeout_seconds: 超时时间（秒）
    """
    for i in range(timeout_seconds):
        await asyncio.sleep(1)

        try:
            with open(feedback_path, "r", encoding="utf-8") as f:
                feedback = json.load(f)

            if feedback.get("decision"):
                logger.info(
                    f"反馈处理完成: {feedback['id']}, "
                    f"decision: {feedback['decision']}"
                )
                await _send_completion_notifications(feedback)
                await _archive_feedback(feedback_path)
                return

        except json.JSONDecodeError as e:
            logger.error(f"解析反馈 JSON 失败: {e}")
        except Exception as e:
            logger.error(f"读取反馈文件失败: {e}")

    # 超时
    logger.warning(
        f"反馈处理超时: {feedback_path}, "
        f"等待了 {timeout_seconds} 秒"
    )
    # 重置为 pending
    update_feedback_status(feedback_path, "pending")


async def _send_completion_notifications(feedback: dict) -> None:
    """
    发送处理完成通知

    包括：
    1. 发送给提出者（通过 source_session）
    2. 发送给维护者（通过 delivery.recipients）

    Args:
        feedback: 反馈数据
    """
    config = load_feedback_config()

    # 1. 发送给提出者
    await _notify_submitter(feedback)

    # 2. 发送给维护者
    await _notify_maintainers(feedback, config)


async def _notify_submitter(feedback: dict) -> None:
    """
    发送结果消息给提出者

    Args:
        feedback: 反馈数据
    """
    source_session = feedback.get("source_session")
    if not source_session:
        logger.warning(f"反馈缺少 source_session: {feedback['id']}")
        return

    decision = feedback.get("decision", "待讨论")
    reason = feedback.get("reason", "")

    message = f"""📊 您的反馈已处理

反馈：{feedback['content'][:100]}{'...' if len(feedback['content']) > 100 else ''}
结果：{decision}
理由：{reason[:100]}{'...' if len(reason) > 100 else reason}
"""

    try:
        client = await get_gateway_client()
        # 通过 session key 发送消息（这里简化处理，实际可能需要其他机制）
        logger.info(f"（TODO）发送结果消息给提出者: {source_session}")
        # TODO: 实现通过 session key 发送消息
    except Exception as e:
        logger.error(f"发送结果消息给提出者失败: {e}")


async def _notify_maintainers(feedback: dict, config) -> None:
    """
    发送通知给维护者

    Args:
        feedback: 反馈数据
        config: 模块配置
    """
    recipients = config.delivery.recipients

    if not recipients:
        return

    decision = feedback.get("decision", "待讨论")
    reason = feedback.get("reason", "")
    source_user = feedback.get("source_user", "系统")
    source_channel = feedback.get("source_channel", "")
    source_info = f"{source_user} ({source_channel})" if source_channel else source_user

    message = f"""📊 反馈处理完成

ID：{feedback['id']}
来源：{source_info}
结果：{decision}
理由：{reason[:100]}{'...' if len(reason) > 100 else reason}
"""

    try:
        client = await get_gateway_client()
        for recipient in recipients:
            result = await client.send_message(
                channel=recipient.channel,
                to=recipient.name,
                message=message,
                account_id=recipient.agent_id,
            )
            if result.get("ok"):
                logger.info(f"通知已发送: {recipient.name}")
            else:
                logger.warning(f"通知发送失败: {recipient.name}")
    except Exception as e:
        logger.error(f"发送维护者通知失败: {e}")


async def _archive_feedback(feedback_path: Path) -> None:
    """
    归档反馈文件（从 new/ 移到 done/）

    Args:
        feedback_path: 反馈 JSON 文件路径
    """
    done_dir = get_feedback_dir(subdir="done")
    done_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 移动文件
        target = done_dir / feedback_path.name
        feedback_path.rename(target)
        logger.info(f"反馈已归档: {feedback_path.name} -> {target}")
    except Exception as e:
        logger.error(f"归档反馈失败: {e}")
