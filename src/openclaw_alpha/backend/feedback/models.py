# -*- coding: utf-8 -*-
"""用户反馈处理模块数据模型"""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field


@dataclass
class FeedbackItem:
    """
    用户反馈数据模型

    Attributes:
        id: 反馈 ID（content hash）
        submitted_at: 提交时间
        content: 提出者的反馈原文
        status: 状态
        source_user: 提交用户（可选）
        source_channel: 提交渠道（可选）
        source_session: 来源 session key（可选）
        background: 背景简述（可选）
        task_dir: 任务目录（处理中）
        job_id: Cron 任务 ID（处理中）
        session_id: Session ID（处理中）
        context_path: Session 文件路径（处理中）
        context_path_deleted: Session 备份路径（处理中）
        started_at: 开始处理时间（处理中）
        decision: 决策结果（处理完成）
        reason: 决策理由（处理完成）
        completed_at: 完成时间（处理完成）
    """

    # 必需字段
    id: str
    submitted_at: str
    content: str
    status: Literal["pending", "processing", "completed"]

    # 可选字段 - 提交时
    source_user: str | None = None
    source_channel: str | None = None
    source_session: str | None = None
    background: str | None = None

    # 可选字段 - 处理中
    task_dir: str | None = None
    job_id: str | None = None
    session_id: str | None = None
    context_path: str | None = None
    context_path_deleted: str | None = None
    started_at: str | None = None

    # 可选字段 - 处理完成
    decision: Literal["采纳", "调整后采纳", "不采纳", "待讨论"] | None = None
    reason: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> dict:
        """转换为字典（用于 JSON 序列化）"""
        result = {
            "id": self.id,
            "submitted_at": self.submitted_at,
            "content": self.content,
            "status": self.status,
        }

        # 可选字段（只在有值时添加）
        if self.source_user:
            result["source_user"] = self.source_user
        if self.source_channel:
            result["source_channel"] = self.source_channel
        if self.source_session:
            result["source_session"] = self.source_session
        if self.background:
            result["background"] = self.background

        # 处理中字段
        if self.task_dir:
            result["task_dir"] = self.task_dir
        if self.job_id:
            result["job_id"] = self.job_id
        if self.session_id:
            result["session_id"] = self.session_id
        if self.context_path:
            result["context_path"] = self.context_path
        if self.context_path_deleted:
            result["context_path_deleted"] = self.context_path_deleted
        if self.started_at:
            result["started_at"] = self.started_at

        # 处理完成字段
        if self.decision:
            result["decision"] = self.decision
        if self.reason:
            result["reason"] = self.reason
        if self.completed_at:
            result["completed_at"] = self.completed_at

        return result

    @classmethod
    def from_dict(cls, data: dict) -> "FeedbackItem":
        """从字典创建（用于 JSON 反序列化）"""
        return cls(
            id=data["id"],
            submitted_at=data["submitted_at"],
            content=data["content"],
            status=data["status"],
            source_user=data.get("source_user"),
            source_channel=data.get("source_channel"),
            source_session=data.get("source_session"),
            background=data.get("background"),
            task_dir=data.get("task_dir"),
            job_id=data.get("job_id"),
            session_id=data.get("session_id"),
            context_path=data.get("context_path"),
            context_path_deleted=data.get("context_path_deleted"),
            started_at=data.get("started_at"),
            decision=data.get("decision"),
            reason=data.get("reason"),
            completed_at=data.get("completed_at"),
        )


class FeedbackQuery(BaseModel):
    """
    反馈查询条件

    用于筛选需要处理的反馈
    """

    status: Literal["pending", "processing", "completed"] | None = Field(
        default=None,
        description="状态过滤",
    )
    source_user: str | None = Field(default=None, description="用户过滤")
    limit: int = Field(default=10, description="最多返回条数，0 表示全部")
