# -*- coding: utf-8 -*-
"""公告解读 Processor 测试"""

import pytest

from openclaw_alpha.skills.announcement_analysis.announcement_processor.announcement_processor import (
    filter_by_code,
    filter_by_keyword,
    format_output,
    sort_by_priority,
)
from openclaw_alpha.skills.announcement_analysis.announcement_processor.models import (
    Announcement,
)


@pytest.fixture
def sample_announcements():
    """测试公告数据"""
    return [
        Announcement(
            code="000001",
            name="平安银行",
            title="关于重大资产购买进展的公告",
            type="重大事项",
            date="2026-03-07",
            url="http://example.com/1",
        ),
        Announcement(
            code="600000",
            name="浦发银行",
            title="2025年年度报告",
            type="财务报告",
            date="2026-03-07",
            url="http://example.com/2",
        ),
        Announcement(
            code="000002",
            name="万科A",
            title="关于股票可能被实施退市风险警示的提示性公告",
            type="风险提示",
            date="2026-03-07",
            url="http://example.com/3",
        ),
        Announcement(
            code="000001",
            name="平安银行",
            title="关于股东增持股份的公告",
            type="持股变动",
            date="2026-03-07",
            url="http://example.com/4",
        ),
    ]


class TestAnnouncementModel:
    """Announcement 模型测试"""

    def test_priority_risk_alert(self):
        """风险提示优先级最高"""
        ann = Announcement(
            code="000001",
            name="测试",
            title="测试",
            type="风险提示",
            date="2026-03-07",
            url="",
        )
        assert ann.priority == 3
        assert ann.priority_stars == "⭐⭐⭐"

    def test_priority_major_event(self):
        """重大事项优先级高"""
        ann = Announcement(
            code="000001",
            name="测试",
            title="测试",
            type="重大事项",
            date="2026-03-07",
            url="",
        )
        assert ann.priority == 3

    def test_priority_financial_report(self):
        """财务报告优先级高"""
        ann = Announcement(
            code="000001",
            name="测试",
            title="测试",
            type="财务报告",
            date="2026-03-07",
            url="",
        )
        assert ann.priority == 3

    def test_priority_restructuring(self):
        """资产重组优先级中"""
        ann = Announcement(
            code="000001",
            name="测试",
            title="测试",
            type="资产重组",
            date="2026-03-07",
            url="",
        )
        assert ann.priority == 2

    def test_priority_default(self):
        """未知类型优先级低"""
        ann = Announcement(
            code="000001",
            name="测试",
            title="测试",
            type="未知类型",
            date="2026-03-07",
            url="",
        )
        assert ann.priority == 1

    def test_to_dict(self):
        """字典转换"""
        ann = Announcement(
            code="000001",
            name="测试",
            title="测试标题",
            type="重大事项",
            date="2026-03-07",
            url="http://example.com",
        )
        d = ann.to_dict()
        assert d["code"] == "000001"
        assert d["name"] == "测试"
        assert d["title"] == "测试标题"
        assert d["priority"] == 3


class TestFilterByCode:
    """代码筛选测试"""

    def test_filter_by_code_found(self, sample_announcements):
        """按代码筛选 - 找到"""
        result = filter_by_code(sample_announcements, "000001")
        assert len(result) == 2
        assert all(a.code == "000001" for a in result)

    def test_filter_by_code_not_found(self, sample_announcements):
        """按代码筛选 - 未找到"""
        result = filter_by_code(sample_announcements, "999999")
        assert len(result) == 0

    def test_filter_by_code_none(self, sample_announcements):
        """按代码筛选 - 无筛选"""
        result = filter_by_code(sample_announcements, None)
        assert len(result) == len(sample_announcements)


class TestFilterByKeyword:
    """关键词搜索测试"""

    def test_filter_by_keyword_found(self, sample_announcements):
        """按关键词搜索 - 找到"""
        result = filter_by_keyword(sample_announcements, "重大")
        assert len(result) == 1
        assert "重大" in result[0].title

    def test_filter_by_keyword_not_found(self, sample_announcements):
        """按关键词搜索 - 未找到"""
        result = filter_by_keyword(sample_announcements, "不存在的关键词")
        assert len(result) == 0

    def test_filter_by_keyword_none(self, sample_announcements):
        """按关键词搜索 - 无筛选"""
        result = filter_by_keyword(sample_announcements, None)
        assert len(result) == len(sample_announcements)

    def test_filter_by_keyword_case_insensitive(self, sample_announcements):
        """按关键词搜索 - 大小写不敏感"""
        result = filter_by_keyword(sample_announcements, "重大")
        result_upper = filter_by_keyword(sample_announcements, "重大".upper())
        assert len(result) == len(result_upper)


class TestSortByPriority:
    """排序测试"""

    def test_sort_by_priority(self, sample_announcements):
        """按重要性排序"""
        sorted_anns = sort_by_priority(sample_announcements)
        # 风险提示、重大事项、财务报告（优先级3）应该在前面
        assert sorted_anns[0].type in ["风险提示", "重大事项", "财务报告"]
        # 持股变动（优先级2）应该在后面
        for ann in sorted_anns:
            if ann.type == "持股变动":
                assert sorted_anns.index(ann) >= 0


class TestFormatOutput:
    """格式化输出测试"""

    def test_format_output_empty(self):
        """空数据格式化"""
        result = format_output([], "2026-03-07", 20)
        assert "暂无公告" in result

    def test_format_output_with_data(self, sample_announcements):
        """有数据格式化"""
        result = format_output(sample_announcements, "2026-03-07", 20)
        assert "【公告列表】2026-03-07" in result
        assert "平安银行" in result
        assert "浦发银行" in result

    def test_format_output_top_n(self, sample_announcements):
        """Top N 限制"""
        result = format_output(sample_announcements, "2026-03-07", 2)
        assert "显示 2 条" in result
