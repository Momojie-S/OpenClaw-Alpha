# -*- coding: utf-8 -*-
"""反馈数据模型测试"""

import pytest

from openclaw_alpha.backend.feedback.models import FeedbackItem, FeedbackQuery


class TestFeedbackItem:
    """反馈数据模型测试"""

    def test_full_item(self):
        """完整字段测试"""
        item = FeedbackItem(
            id="abc123",
            source_user="Momojie",
            source_channel="wecom",
            source_session="session:key",
            submitted_at="2026-03-18T10:00:00+08:00",
            background="背景简述",
            content="反馈内容",
            status="pending",
        )

        data = item.to_dict()

        assert data["id"] == "abc123"
        assert data["source_user"] == "Momojie"
        assert data["source_channel"] == "wecom"
        assert data["source_session"] == "session:key"
        assert data["background"] == "背景简述"
        assert data["content"] == "反馈内容"
        assert data["status"] == "pending"

    def test_minimal_item(self):
        """最小字段测试（可选字段全为空）"""
        item = FeedbackItem(
            id="abc123",
            submitted_at="2026-03-18T10:00:00+08:00",
            content="反馈内容",
            status="pending",
        )

        data = item.to_dict()

        assert data["id"] == "abc123"
        assert data["content"] == "反馈内容"
        assert data["status"] == "pending"

        # 可选字段不应该出现
        assert "source_user" not in data
        assert "source_channel" not in data
        assert "source_session" not in data
        assert "background" not in data

    def test_from_dict_full(self):
        """从完整字典创建"""
        data = {
            "id": "abc123",
            "source_user": "Momojie",
            "source_channel": "wecom",
            "source_session": "session:key",
            "submitted_at": "2026-03-18T10:00:00+08:00",
            "background": "背景简述",
            "content": "反馈内容",
            "status": "pending",
        }

        item = FeedbackItem.from_dict(data)

        assert item.id == "abc123"
        assert item.source_user == "Momojie"
        assert item.background == "背景简述"
        assert item.content == "反馈内容"

    def test_from_dict_minimal(self):
        """从最小字典创建（无可选字段）"""
        data = {
            "id": "abc123",
            "submitted_at": "2026-03-18T10:00:00+08:00",
            "content": "反馈内容",
            "status": "pending",
        }

        item = FeedbackItem.from_dict(data)

        assert item.id == "abc123"
        assert item.source_user is None
        assert item.source_channel is None
        assert item.source_session is None
        assert item.background is None

    def test_roundtrip_serialization(self):
        """序列化和反序列化往返测试"""
        original = FeedbackItem(
            id="abc123",
            source_user="Momojie",
            background="背景",
            content="内容",
            submitted_at="2026-03-18T10:00:00+08:00",
            status="processing",
            task_dir="/path/to/task",
            job_id="job-123",
        )

        # 序列化 -> 反序列化
        data = original.to_dict()
        restored = FeedbackItem.from_dict(data)

        assert restored.id == original.id
        assert restored.source_user == original.source_user
        assert restored.background == original.background
        assert restored.content == original.content
        assert restored.task_dir == original.task_dir
        assert restored.job_id == original.job_id

    def test_processing_fields(self):
        """处理中字段测试"""
        item = FeedbackItem(
            id="abc123",
            submitted_at="2026-03-18T10:00:00+08:00",
            content="反馈内容",
            status="processing",
            task_dir="/path/to/task",
            job_id="job-123",
            session_id="session-456",
            context_path="/path/to/session.jsonl",
            context_path_deleted="/path/to/session.deleted.*",
            started_at="2026-03-18T10:05:00+08:00",
        )

        data = item.to_dict()

        assert data["task_dir"] == "/path/to/task"
        assert data["job_id"] == "job-123"
        assert data["session_id"] == "session-456"
        assert data["started_at"] == "2026-03-18T10:05:00+08:00"

    def test_completed_fields(self):
        """处理完成字段测试"""
        item = FeedbackItem(
            id="abc123",
            submitted_at="2026-03-18T10:00:00+08:00",
            content="反馈内容",
            status="completed",
            decision="采纳",
            reason="需求合理",
            completed_at="2026-03-18T10:10:00+08:00",
        )

        data = item.to_dict()

        assert data["decision"] == "采纳"
        assert data["reason"] == "需求合理"
        assert data["completed_at"] == "2026-03-18T10:10:00+08:00"


class TestFeedbackQuery:
    """反馈查询模型测试"""

    def test_default_values(self):
        """默认值测试"""
        query = FeedbackQuery()
        assert query.status is None
        assert query.source_user is None
        assert query.limit == 10

    def test_with_filters(self):
        """带过滤条件"""
        query = FeedbackQuery(status="pending", source_user="Momojie", limit=5)
        assert query.status == "pending"
        assert query.source_user == "Momojie"
        assert query.limit == 5
