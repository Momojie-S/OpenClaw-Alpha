# -*- coding: utf-8 -*-
"""反馈定时任务测试"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openclaw_alpha.backend.feedback.jobs import scan_pending_feedback


class TestScanPendingFeedback:
    """扫描待处理反馈测试"""

    def test_scan_pending(self, tmp_path):
        """扫描待处理反馈"""
        feedback_dir = tmp_path / "workspace" / "feedback" / "new"
        feedback_dir.mkdir(parents=True)

        # 创建 pending 反馈
        pending_feedback = {
            "id": "pending-1",
            "content": "待处理反馈",
            "submitted_at": "2026-03-18T10:00:00+08:00",
            "status": "pending",
        }
        with open(feedback_dir / "pending-1.json", "w") as f:
            json.dump(pending_feedback, f)

        # 创建 processing 反馈
        processing_feedback = {
            "id": "processing-1",
            "content": "处理中反馈",
            "submitted_at": "2026-03-18T10:00:00+08:00",
            "status": "processing",
        }
        with open(feedback_dir / "processing-1.json", "w") as f:
            json.dump(processing_feedback, f)

        # 创建 completed 反馈
        completed_feedback = {
            "id": "completed-1",
            "content": "已完成反馈",
            "submitted_at": "2026-03-18T10:00:00+08:00",
            "status": "completed",
        }
        with open(feedback_dir / "completed-1.json", "w") as f:
            json.dump(completed_feedback, f)

        # 扫描
        result = scan_pending_feedback(limit=0, project_root=tmp_path)

        assert len(result) == 1
        assert result[0].name == "pending-1.json"

    def test_scan_with_limit(self, tmp_path):
        """扫描带数量限制"""
        feedback_dir = tmp_path / "workspace" / "feedback" / "new"
        feedback_dir.mkdir(parents=True)

        # 创建多个 pending 反馈
        for i in range(5):
            feedback = {
                "id": f"pending-{i}",
                "content": f"反馈{i}",
                "submitted_at": "2026-03-18T10:00:00+08:00",
                "status": "pending",
            }
            with open(feedback_dir / f"pending-{i}.json", "w") as f:
                json.dump(feedback, f)

        # 扫描，限制 2 条
        result = scan_pending_feedback(limit=2, project_root=tmp_path)

        assert len(result) == 2

    def test_scan_empty_dir(self, tmp_path):
        """空目录应该返回空列表"""
        feedback_dir = tmp_path / "workspace" / "feedback" / "new"
        feedback_dir.mkdir(parents=True)

        result = scan_pending_feedback(limit=0, project_root=tmp_path)

        assert len(result) == 0

    def test_scan_nonexistent_dir(self, tmp_path):
        """目录不存在应该返回空列表"""
        result = scan_pending_feedback(limit=0, project_root=tmp_path)

        assert len(result) == 0

    def test_scan_skip_invalid_json(self, tmp_path):
        """应该跳过损坏的 JSON 文件"""
        feedback_dir = tmp_path / "workspace" / "feedback" / "new"
        feedback_dir.mkdir(parents=True)

        # 创建有效反馈
        valid_feedback = {
            "id": "valid-1",
            "content": "有效反馈",
            "submitted_at": "2026-03-18T10:00:00+08:00",
            "status": "pending",
        }
        with open(feedback_dir / "valid.json", "w") as f:
            json.dump(valid_feedback, f)

        # 创建损坏的 JSON
        with open(feedback_dir / "invalid.json", "w") as f:
            f.write("{ invalid json }")

        # 扫描应该只返回有效的
        result = scan_pending_feedback(limit=0, project_root=tmp_path)

        assert len(result) == 1
        assert result[0].name == "valid.json"


class TestProcessFeedback:
    """处理反馈测试（mock 提交任务）"""

    @pytest.mark.asyncio
    async def test_process_calls_submit(self, tmp_path):
        """处理应该调用 submit_feedback_task"""
        feedback_dir = tmp_path / "workspace" / "feedback" / "new"
        feedback_dir.mkdir(parents=True)

        # 创建 pending 反馈
        feedback = {
            "id": "test-1",
            "content": "测试反馈",
            "submitted_at": "2026-03-18T10:00:00+08:00",
            "status": "pending",
        }
        feedback_file = feedback_dir / "test-1.json"
        with open(feedback_file, "w") as f:
            json.dump(feedback, f)

        with patch(
            "openclaw_alpha.backend.feedback.jobs.submit_feedback_task",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_submit, patch(
            "openclaw_alpha.backend.feedback.jobs.load_feedback_config",
            return_value=MagicMock(enabled=True),
        ):
            from openclaw_alpha.backend.feedback.jobs import process_feedback

            await process_feedback(limit=1, project_root=tmp_path)

            mock_submit.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_disabled(self, tmp_path):
        """模块禁用时不应该处理"""
        with patch(
            "openclaw_alpha.backend.feedback.jobs.load_feedback_config",
            return_value=MagicMock(enabled=False),
        ):
            from openclaw_alpha.backend.feedback.jobs import process_feedback

            # 应该直接返回，不抛异常
            await process_feedback(limit=1, project_root=tmp_path)
