# -*- coding: utf-8 -*-
"""反馈提交模块测试"""

import hashlib
import json
from pathlib import Path

import pytest

from openclaw_alpha.backend.feedback.submit_feedback import (
    construct_feedback_json,
    generate_feedback_id,
    get_current_time_iso,
    save_feedback_file,
    submit_feedback,
)


class TestGenerateFeedbackId:
    """反馈 ID 生成测试"""

    def test_id_is_sha256(self):
        """ID 应该是 SHA256 hash"""
        content = "测试反馈"
        expected = hashlib.sha256(content.encode("utf-8")).hexdigest()
        assert generate_feedback_id(content) == expected

    def test_same_content_same_id(self):
        """相同内容生成相同 ID"""
        content = "测试反馈"
        id1 = generate_feedback_id(content)
        id2 = generate_feedback_id(content)
        assert id1 == id2

    def test_different_content_different_id(self):
        """不同内容生成不同 ID"""
        id1 = generate_feedback_id("反馈A")
        id2 = generate_feedback_id("反馈B")
        assert id1 != id2

    def test_empty_content(self):
        """空内容也生成有效 ID"""
        feedback_id = generate_feedback_id("")
        assert len(feedback_id) == 64


class TestConstructFeedbackJson:
    """反馈 JSON 构造测试"""

    def test_required_fields(self):
        """必需字段应该存在"""
        json_data = construct_feedback_json(content="测试反馈")
        assert "id" in json_data
        assert "submitted_at" in json_data
        assert json_data["content"] == "测试反馈"
        assert json_data["status"] == "pending"

    def test_all_optional_fields(self):
        """所有可选字段都提供时应该全部包含"""
        json_data = construct_feedback_json(
            content="测试反馈",
            background="背景简述",
            source_user="Momojie",
            source_channel="wecom",
            source_session="session:key",
        )
        assert json_data["background"] == "背景简述"
        assert json_data["source_user"] == "Momojie"
        assert json_data["source_channel"] == "wecom"
        assert json_data["source_session"] == "session:key"

    def test_no_optional_fields(self):
        """不提供可选字段时不应该包含"""
        json_data = construct_feedback_json(content="测试反馈")
        assert "background" not in json_data
        assert "source_user" not in json_data
        assert "source_channel" not in json_data
        assert "source_session" not in json_data

    def test_partial_optional_fields(self):
        """只提供部分可选字段"""
        json_data = construct_feedback_json(
            content="测试反馈",
            source_user="Momojie",
            # 不提供 source_channel 和 source_session
        )
        assert json_data["source_user"] == "Momojie"
        assert "source_channel" not in json_data
        assert "source_session" not in json_data


class TestSaveFeedbackFile:
    """反馈文件保存测试"""

    def test_save_file(self, tmp_path):
        """文件应该正确保存"""
        json_data = construct_feedback_json(content="测试反馈")
        file_path = save_feedback_file(json_data, tmp_path)

        assert file_path.exists()
        assert file_path.suffix == ".json"

        with open(file_path, "r", encoding="utf-8") as f:
            saved = json.load(f)

        assert saved["content"] == "测试反馈"
        assert saved["status"] == "pending"

    def test_file_naming(self, tmp_path):
        """文件名应该符合 YYYY-MM-DD-{hash}.json 格式"""
        json_data = construct_feedback_json(content="测试反馈")
        file_path = save_feedback_file(json_data, tmp_path)

        # 文件名应该包含日期和 hash
        name = file_path.stem
        parts = name.split("-")
        # 日期部分：YYYY, MM, DD
        assert len(parts[0]) == 4
        assert len(parts[1]) == 2
        assert len(parts[2]) == 2
        # hash 部分（12位）
        assert len(parts[3]) == 12


class TestSubmitFeedback:
    """提交反馈集成测试"""

    def test_submit_success(self, tmp_path):
        """提交成功应该返回 success=True"""
        result = submit_feedback(
            content="测试反馈",
            source_user="Momojie",
            source_channel="wecom",
            source_session="session:key",
            project_root=tmp_path,
        )

        assert result["success"] is True
        assert result["feedback_id"]
        assert result["file_path"]
        assert result["error"] is None

        # 验证文件存在
        file_path = Path(result["file_path"])
        assert file_path.exists()

    def test_submit_without_optional_fields(self, tmp_path):
        """不提供可选字段也能提交成功"""
        result = submit_feedback(
            content="测试反馈",
            project_root=tmp_path,
        )

        assert result["success"] is True

        # 验证文件内容
        file_path = Path(result["file_path"])
        with open(file_path, "r", encoding="utf-8") as f:
            saved = json.load(f)

        assert "source_user" not in saved
        assert "source_channel" not in saved
        assert "source_session" not in saved


class TestGetCurrentTimeIso:
    """时间格式测试"""

    def test_iso_format(self):
        """时间应该返回 ISO 8601 格式"""
        time_str = get_current_time_iso()
        assert "T" in time_str
        assert "+" in time_str  # 时区信息
