# -*- coding: utf-8 -*-
"""限售解禁风险监控 Processor 测试"""

import pytest

from openclaw_alpha.skills.restricted_release.restricted_release_processor.restricted_release_processor import (
    format_upcoming,
    format_queue,
    format_high_risk,
)


class TestFormatUpcoming:
    """测试 format_upcoming 函数"""

    def test_format_empty_list(self):
        """测试空列表"""
        result = format_upcoming([])
        assert "共 0 只" in result

    def test_format_with_data(self):
        """测试有数据"""
        data = [
            {
                "code": "600000",
                "name": "浦发银行",
                "release_date": "2026-03-15",
                "actual_release_value": 500000000,  # 5亿
                "ratio_to_circulation": 0.15,
            },
            {
                "code": "000001",
                "name": "平安银行",
                "release_date": "2026-03-16",
                "actual_release_value": 1000000000,  # 10亿
                "ratio_to_circulation": 0.20,
            },
        ]
        result = format_upcoming(data)

        assert "共 2 只" in result
        assert "600000" in result
        assert "浦发银行" in result
        assert "000001" in result
        assert "平安银行" in result

    def test_format_columns(self):
        """测试列名"""
        data = [{"code": "600000", "name": "浦发银行", "release_date": "2026-03-15", "actual_release_value": 500000000, "ratio_to_circulation": 0.15}]
        result = format_upcoming(data)

        assert "代码" in result
        assert "名称" in result
        assert "解禁日期" in result
        assert "解禁市值" in result


class TestFormatQueue:
    """测试 format_queue 函数"""

    def test_format_empty_list(self):
        """测试空列表"""
        result = format_queue([])
        assert "共 0 次" in result

    def test_format_with_data(self):
        """测试有数据"""
        data = [
            {
                "release_date": "2026-03-15",
                "shareholder_count": 5,
                "actual_release_value": 500000000,
                "ratio_to_circulation": 0.15,
                "restricted_type": "定向增发",
            },
        ]
        result = format_queue(data)

        assert "共 1 次" in result
        assert "2026-03-15" in result
        assert "5" in result  # 股东数

    def test_format_columns(self):
        """测试列名"""
        data = [{"release_date": "2026-03-15", "shareholder_count": 5, "actual_release_value": 500000000, "ratio_to_circulation": 0.15, "restricted_type": "定向增发"}]
        result = format_queue(data)

        assert "解禁日期" in result
        assert "股东数" in result
        assert "类型" in result


class TestFormatHighRisk:
    """测试 format_high_risk 函数"""

    def test_format_empty_list(self):
        """测试空列表"""
        result = format_high_risk([], 0.1)
        assert "无高风险股票" in result

    def test_format_with_data(self):
        """测试有数据"""
        data = [
            {
                "code": "600000",
                "name": "浦发银行",
                "release_date": "2026-03-15",
                "actual_release_value": 500000000,
                "ratio_to_circulation": 0.55,  # 55%
            },
        ]
        result = format_high_risk(data, 0.1)

        assert "共 1 只" in result
        assert "600000" in result
        assert "极高" in result  # >=50% 是极高

    def test_risk_level_extreme(self):
        """测试极高风险等级"""
        data = [{"code": "600000", "name": "浦发银行", "release_date": "2026-03-15", "actual_release_value": 500000000, "ratio_to_circulation": 0.55}]
        result = format_high_risk(data, 0.1)
        assert "极高" in result

    def test_risk_level_high(self):
        """测试高风险等级"""
        data = [{"code": "600000", "name": "浦发银行", "release_date": "2026-03-15", "actual_release_value": 500000000, "ratio_to_circulation": 0.35}]
        result = format_high_risk(data, 0.1)
        assert "高" in result

    def test_risk_level_medium(self):
        """测试中风险等级"""
        data = [{"code": "600000", "name": "浦发银行", "release_date": "2026-03-15", "actual_release_value": 500000000, "ratio_to_circulation": 0.25}]
        result = format_high_risk(data, 0.1)
        assert "中" in result

    def test_risk_level_low(self):
        """测试低风险等级"""
        data = [{"code": "600000", "name": "浦发银行", "release_date": "2026-03-15", "actual_release_value": 500000000, "ratio_to_circulation": 0.15}]
        result = format_high_risk(data, 0.1)
        assert "低" in result
