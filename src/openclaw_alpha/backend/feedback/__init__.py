# -*- coding: utf-8 -*-
"""用户反馈处理模块

提供用户反馈收集、处理、通知等功能。

关联文档：
- 设计文档：docs/design/feedback/overview.md
- 流程文档：docs/workflow/feedback-workflow.md
"""

from .config import FeedbackConfig, load_feedback_config
from .models import FeedbackItem, FeedbackQuery

__all__ = [
    "FeedbackConfig",
    "load_feedback_config",
    "FeedbackItem",
    "FeedbackQuery",
]
