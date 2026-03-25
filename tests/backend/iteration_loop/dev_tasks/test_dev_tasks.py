# -*- coding: utf-8 -*-
"""dev_tasks 子模块测试"""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import tempfile
import shutil

from openclaw_alpha.backend.iteration_loop.dev_tasks import (
    _run_openspec_list,
    _check_change_completeness,
    _find_complete_changes,
    _select_random_change,
    _build_message,
    process,
)


class TestRunOpenspecList:
    """测试 _run_openspec_list"""

    @patch("subprocess.run")
    def test_success(self, mock_run):
        """成功获取 changes"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps({"changes": ["change-1", "change-2"]}),
            stderr="",
        )

        result = _run_openspec_list()
        assert result == ["change-1", "change-2"]

    @patch("subprocess.run")
    def test_empty_changes(self, mock_run):
        """返回空列表"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps({"changes": []}),
            stderr="",
        )

        result = _run_openspec_list()
        assert result == []

    @patch("subprocess.run")
    def test_openspec_not_installed(self, mock_run):
        """openspec 未安装"""
        mock_run.side_effect = FileNotFoundError()

        result = _run_openspec_list()
        assert result == []

    @patch("subprocess.run")
    def test_json_parse_error(self, mock_run):
        """JSON 解析失败"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="invalid json",
            stderr="",
        )

        result = _run_openspec_list()
        assert result == []

    @patch("subprocess.run")
    def test_openspec_error(self, mock_run):
        """openspec 命令失败"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="error",
        )

        result = _run_openspec_list()
        assert result == []

    @patch("subprocess.run")
    def test_timeout(self, mock_run):
        """命令超时"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="openspec", timeout=30)

        result = _run_openspec_list()
        assert result == []


class TestCheckChangeCompleteness:
    """测试 _check_change_completeness"""

    def test_complete_change(self, tmp_path):
        """完整的 change"""
        change_dir = tmp_path / "openspec" / "changes" / "test-change"
        change_dir.mkdir(parents=True)

        # 创建必需文件
        (change_dir / "proposal.md").write_text("# Proposal")
        (change_dir / "design.md").write_text("# Design")

        specs_dir = change_dir / "specs"
        specs_dir.mkdir()
        (specs_dir / "spec.md").write_text("# Spec")

        (change_dir / "tasks.md").write_text("- [ ] Task 1\n- [x] Task 2")

        with patch(
            "openclaw_alpha.backend.iteration_loop.dev_tasks.OPENSPEC_PROJECT_DIR",
            tmp_path,
        ):
            result = _check_change_completeness("test-change")
            assert result is True

    def test_missing_proposal(self, tmp_path):
        """缺少 proposal.md"""
        change_dir = tmp_path / "openspec" / "changes" / "test-change"
        change_dir.mkdir(parents=True)

        (change_dir / "design.md").write_text("# Design")
        specs_dir = change_dir / "specs"
        specs_dir.mkdir()
        (specs_dir / "spec.md").write_text("# Spec")
        (change_dir / "tasks.md").write_text("- [ ] Task 1")

        with patch(
            "openclaw_alpha.backend.iteration_loop.dev_tasks.OPENSPEC_PROJECT_DIR",
            tmp_path,
        ):
            result = _check_change_completeness("test-change")
            assert result is False

    def test_missing_design(self, tmp_path):
        """缺少 design.md"""
        change_dir = tmp_path / "openspec" / "changes" / "test-change"
        change_dir.mkdir(parents=True)

        (change_dir / "proposal.md").write_text("# Proposal")
        specs_dir = change_dir / "specs"
        specs_dir.mkdir()
        (specs_dir / "spec.md").write_text("# Spec")
        (change_dir / "tasks.md").write_text("- [ ] Task 1")

        with patch(
            "openclaw_alpha.backend.iteration_loop.dev_tasks.OPENSPEC_PROJECT_DIR",
            tmp_path,
        ):
            result = _check_change_completeness("test-change")
            assert result is False

    def test_missing_specs(self, tmp_path):
        """缺少 specs 目录"""
        change_dir = tmp_path / "openspec" / "changes" / "test-change"
        change_dir.mkdir(parents=True)

        (change_dir / "proposal.md").write_text("# Proposal")
        (change_dir / "design.md").write_text("# Design")
        (change_dir / "tasks.md").write_text("- [ ] Task 1")

        with patch(
            "openclaw_alpha.backend.iteration_loop.dev_tasks.OPENSPEC_PROJECT_DIR",
            tmp_path,
        ):
            result = _check_change_completeness("test-change")
            assert result is False

    def test_empty_specs(self, tmp_path):
        """specs 目录为空"""
        change_dir = tmp_path / "openspec" / "changes" / "test-change"
        change_dir.mkdir(parents=True)

        (change_dir / "proposal.md").write_text("# Proposal")
        (change_dir / "design.md").write_text("# Design")
        (change_dir / "specs").mkdir()
        (change_dir / "tasks.md").write_text("- [ ] Task 1")

        with patch(
            "openclaw_alpha.backend.iteration_loop.dev_tasks.OPENSPEC_PROJECT_DIR",
            tmp_path,
        ):
            result = _check_change_completeness("test-change")
            assert result is False

    def test_no_incomplete_tasks(self, tmp_path):
        """tasks.md 中没有未完成任务"""
        change_dir = tmp_path / "openspec" / "changes" / "test-change"
        change_dir.mkdir(parents=True)

        (change_dir / "proposal.md").write_text("# Proposal")
        (change_dir / "design.md").write_text("# Design")
        specs_dir = change_dir / "specs"
        specs_dir.mkdir()
        (specs_dir / "spec.md").write_text("# Spec")
        (change_dir / "tasks.md").write_text("- [x] Task 1\n- [x] Task 2")

        with patch(
            "openclaw_alpha.backend.iteration_loop.dev_tasks.OPENSPEC_PROJECT_DIR",
            tmp_path,
        ):
            result = _check_change_completeness("test-change")
            assert result is False

    def test_change_not_exists(self, tmp_path):
        """change 目录不存在"""
        with patch(
            "openclaw_alpha.backend.iteration_loop.dev_tasks.OPENSPEC_PROJECT_DIR",
            tmp_path,
        ):
            result = _check_change_completeness("nonexistent")
            assert result is False


class TestFindCompleteChanges:
    """测试 _find_complete_changes"""

    @patch("openclaw_alpha.backend.iteration_loop.dev_tasks._run_openspec_list")
    @patch("openclaw_alpha.backend.iteration_loop.dev_tasks._check_change_completeness")
    def test_filters_incomplete(self, mock_check, mock_list):
        """过滤不完整的 changes"""
        mock_list.return_value = ["change-1", "change-2", "change-3"]
        mock_check.side_effect = [True, False, True]

        result = _find_complete_changes()
        assert result == ["change-1", "change-3"]

    @patch("openclaw_alpha.backend.iteration_loop.dev_tasks._run_openspec_list")
    def test_empty_list(self, mock_list):
        """没有活跃的 changes"""
        mock_list.return_value = []

        result = _find_complete_changes()
        assert result == []


class TestSelectRandomChange:
    """测试 _select_random_change"""

    def test_selects_from_list(self):
        """从列表中选择"""
        changes = ["change-1", "change-2", "change-3"]
        result = _select_random_change(changes)
        assert result in changes

    def test_empty_list(self):
        """空列表返回 None"""
        result = _select_random_change([])
        assert result is None


class TestBuildMessage:
    """测试 _build_message"""

    def test_message_format(self):
        """消息格式正确"""
        result = _build_message("my-change")
        assert "my-change" in result
        assert "OpenSpec apply" in result


class TestProcess:
    """测试 process 函数"""

    @pytest.mark.asyncio
    @patch("openclaw_alpha.backend.iteration_loop.dev_tasks._find_complete_changes")
    @patch("openclaw_alpha.backend.iteration_loop.dev_tasks._select_random_change")
    @patch("openclaw_alpha.backend.iteration_loop.dev_tasks.submit_cron_task")
    async def test_no_complete_changes(self, mock_submit, mock_select, mock_find):
        """没有完整的 changes"""
        mock_find.return_value = []

        result = await process()
        assert result is False
        mock_submit.assert_not_called()

    @pytest.mark.asyncio
    @patch("openclaw_alpha.backend.iteration_loop.dev_tasks._find_complete_changes")
    @patch("openclaw_alpha.backend.iteration_loop.dev_tasks._select_random_change")
    @patch("openclaw_alpha.backend.iteration_loop.dev_tasks.submit_cron_task")
    async def test_select_returns_none(self, mock_submit, mock_select, mock_find):
        """选择返回 None"""
        mock_find.return_value = ["change-1"]
        mock_select.return_value = None

        result = await process()
        assert result is False
        mock_submit.assert_not_called()

    @pytest.mark.asyncio
    @patch("openclaw_alpha.backend.iteration_loop.dev_tasks._find_complete_changes")
    @patch("openclaw_alpha.backend.iteration_loop.dev_tasks._select_random_change")
    @patch("openclaw_alpha.backend.iteration_loop.dev_tasks.submit_cron_task")
    @patch("openclaw_alpha.backend.iteration_loop.dev_tasks._monitor_session")
    async def test_submit_success(
        self, mock_monitor, mock_submit, mock_select, mock_find
    ):
        """成功提交任务"""
        from dataclasses import dataclass

        @dataclass
        class SubmitResult:
            success: bool
            session_id: str
            error: str = None

        mock_find.return_value = ["change-1"]
        mock_select.return_value = "change-1"
        mock_submit.return_value = SubmitResult(success=True, session_id="session-123")
        mock_monitor.return_value = "completed"

        result = await process()
        assert result is True
        mock_submit.assert_called_once()

    @pytest.mark.asyncio
    @patch("openclaw_alpha.backend.iteration_loop.dev_tasks._find_complete_changes")
    @patch("openclaw_alpha.backend.iteration_loop.dev_tasks._select_random_change")
    @patch("openclaw_alpha.backend.iteration_loop.dev_tasks.submit_cron_task")
    async def test_submit_failure(self, mock_submit, mock_select, mock_find):
        """提交失败"""
        from dataclasses import dataclass

        @dataclass
        class SubmitResult:
            success: bool
            session_id: str
            error: str

        mock_find.return_value = ["change-1"]
        mock_select.return_value = "change-1"
        mock_submit.return_value = SubmitResult(
            success=False, session_id=None, error="Connection failed"
        )

        result = await process()
        assert result is False
