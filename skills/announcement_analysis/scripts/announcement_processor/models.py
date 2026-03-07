# -*- coding: utf-8 -*-
"""公告数据模型"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Announcement:
    """公告信息"""

    code: str  # 股票代码
    name: str  # 股票名称
    title: str  # 公告标题
    type: str  # 公告类型
    date: str  # 发布日期
    url: str  # 公告链接

    @property
    def priority(self) -> int:
        """公告重要性（1-3，3最高）"""
        TYPE_PRIORITY = {
            "风险提示": 3,
            "重大事项": 3,
            "财务报告": 3,
            "资产重组": 2,
            "融资公告": 2,
            "持股变动": 2,
            "信息变更": 1,
        }
        return TYPE_PRIORITY.get(self.type, 1)

    @property
    def priority_stars(self) -> str:
        """重要性星号表示"""
        return "⭐" * self.priority

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "code": self.code,
            "name": self.name,
            "title": self.title,
            "type": self.type,
            "date": self.date,
            "url": self.url,
            "priority": self.priority,
        }
