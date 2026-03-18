# -*- coding: utf-8 -*-
"""反馈任务执行器测试（mock 智能体调用）"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openclaw_alpha.backend.feedback.task_executor import (
    build_message,
    get_feedback_dir,
    get_feedback_task_dir,
    update_feedback_status,
)


class TestGetFeedbackDir:
    """反馈目录获取测试"""

    def test_default_new_dir(self, tmp_path):
        """默认应该返回 new 目录"""
        feedback_dir = get_feedback_dir(project_root=tmp_path, subdir="new")
        assert feedback_dir == tmp_path / "workspace" / "feedback" / "new"

    def test_done_dir(self, tmp_path):
        """done 目录"""
        feedback_dir = get_feedback_dir(project_root=tmp_path, subdir="done")
        assert feedback_dir == tmp_path / "workspace" / "feedback" / "done"


class TestGetFeedbackTaskDir:
    """任务目录获取测试"""

    def test_task_dir_structure(self, tmp_path):
        """任务目录结构应该正确"""
        task_dir = get_feedback_task_dir(
            project_root=tmp_path,
            date="2026-03-18",
            feedback_id="abc123",
        )
        expected = tmp_path / "workspace" / "feedback" / "tasks" / "2026-03-18" / "abc123"
        assert task_dir == expected


class TestUpdateFeedbackStatus:
    """反馈状态更新测试"""

    def test_update_status(self, tmp_path):
        """更新状态"""
        # 创建测试反馈文件
        feedback_file = tmp_path / "test.json"
        feedback = {
            "id": "abc123",
            "content": "测试",
            "submitted_at": "2026-03-18T10:00:00+08:00",
            "status": "pending",
        }
        with open(feedback_file, "w") as f:
            json.dump(feedback, f)

        # 更新状态
        result = update_feedback_status(
            feedback_file,
            "processing",
            job_id="job-123",
        )

        assert result is True

        # 验证更新
        with open(feedback_file, "r") as f:
            updated = json.load(f)

        assert updated["status"] == "processing"
        assert updated["job_id"] == "job-123"


class TestBuildMessage:
    """任务消息构造测试"""

    def test_message_structure(self, tmp_path):
        """消息应该包含模板和参数"""
        # 创建模板文件
        docs_dir = tmp_path / "docs" / "workflow"
        docs_dir.mkdir(parents=True)
        template_file = docs_dir / "feedback-workflow.md"
        template_file.write_text("# 反馈处理流程\n\n处理步骤...")

        # 构造消息（使用临时路径）
        with patch(
            "openclaw_alpha.backend.feedback.task_executor.load_workflow_template",
            return_value="# 反馈处理流程\n\n处理步骤...",
        ):
            message = build_message(
                task_dir="/path/to/task",
                json_path="/path/to/feedback.json",
                feedback_content="测试反馈内容",
            )

        assert "# 反馈处理流程" in message
        assert "/path/to/task" in message
        assert "/path/to/feedback.json" in message
        assert "测试反馈内容" in message


class TestSubmitFeedbackTask:
    """提交反馈任务测试（mock cron 和 gateway）"""

    @pytest.mark.asyncio
    async def test_submit_success(self, tmp_path):
        """成功提交任务"""
        # 创建测试反馈
        feedback_file = tmp_path / "test.json"
        feedback = {
            "id": "abc123",
            "content": "测试反馈",
            "submitted_at": "2026-03-18T10:00:00+08:00",
            "status": "pending",
        }
        with open(feedback_file, "w") as f:
            json.dump(feedback, f)

        # mock cron_utils
        mock_cron_result = MagicMock()
        mock_cron_result.success = True
        mock_cron_result.job_id = "job-123"
        mock_cron_result.session_id = "session-456"
        mock_cron_result.context_path = "/path/to/session.jsonl"
        mock_cron_result.context_path_deleted = "/path/to/session.deleted.*"

        with patch(
            "openclaw_alpha.backend.feedback.task_executor.submit_cron_task",
            new_callable=AsyncMock,
            return_value=mock_cron_result,
        ), patch(
            "openclaw_alpha.backend.feedback.task_executor.load_feedback_config",
            return_value=MagicMock(
                agent_id="alpha",
                model=None,
                cron=MagicMock(
                    session_poll_timeout_seconds=1,
                    result_wait_timeout_seconds=1,
                ),
            ),
        ), patch(
            "openclaw_alpha.backend.feedback.task_executor._wait_for_completion",
            new_callable=AsyncMock,
        ), patch(
            "openclaw_alpha.backend.feedback.task_executor.get_feedback_task_dir",
            return_value=tmp_path / "task",
        ):
            from openclaw_alpha.backend.feedback.task_executor import submit_feedback_task

            result = await submit_feedback_task(feedback_file, feedback)

            assert result is True

    @pytest.mark.asyncio
    async def test_submit_cron_failure(self, tmp_path):
        """Cron 任务失败时应该重置为 pending"""
        feedback_file = tmp_path / "test.json"
        feedback = {
            "id": "abc123",
            "content": "测试反馈",
            "submitted_at": "2026-03-18T10:00:00+08:00",
            "status": "pending",
        }
        with open(feedback_file, "w") as f:
            json.dump(feedback, f)

        mock_cron_result = MagicMock()
        mock_cron_result.success = False
        mock_cron_result.error = "任务执行失败"

        with patch(
            "openclaw_alpha.backend.feedback.task_executor.submit_cron_task",
            new_callable=AsyncMock,
            return_value=mock_cron_result,
        ), patch(
            "openclaw_alpha.backend.feedback.task_executor.load_feedback_config",
            return_value=MagicMock(
                agent_id="alpha",
                model=None,
                cron=MagicMock(session_poll_timeout_seconds=1),
            ),
        ), patch(
            "openclaw_alpha.backend.feedback.task_executor.get_feedback_task_dir",
            return_value=tmp_path / "task",
        ):
            from openclaw_alpha.backend.feedback.task_executor import submit_feedback_task

            result = await submit_feedback_task(feedback_file, feedback)

            assert result is False

            # 验证状态重置为 pending
            with open(feedback_file, "r") as f:
                updated = json.load(f)
            assert updated["status"] == "pending"
