# -*- coding: utf-8 -*-
"""情绪周期可视化测试"""

import pytest
from datetime import datetime

from openclaw_alpha.skills.theme_speculation.sentiment_cycle_processor.sentiment_cycle_processor import (
    SentimentIndicators,
    SentimentCycleResult,
    _generate_ascii_chart,
    format_trend_output,
)


class TestGenerateAsciiChart:
    """测试 ASCII 图表生成"""

    def test_empty_values(self):
        """测试空数据"""
        result = _generate_ascii_chart([])
        assert result == "无数据"

    def test_all_zero_values(self):
        """测试全零数据"""
        result = _generate_ascii_chart([0, 0, 0])
        assert result == "无数据"

    def test_single_value(self):
        """测试单个值"""
        result = _generate_ascii_chart([50])
        assert len(result) > 0
        assert "▄" in result or "█" in result  # 应该有图表字符

    def test_normal_values(self):
        """测试正常数据"""
        values = [10, 20, 30, 40, 50]
        result = _generate_ascii_chart(values, width=10)
        assert len(result) > 0
        # 检查是否包含图表字符
        assert any(char in result for char in ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"])

    def test_all_same_values(self):
        """测试所有值相同"""
        result = _generate_ascii_chart([50, 50, 50, 50])
        assert len(result) > 0
        # 所有值相同,应该使用中等高度
        assert "▄" in result

    def test_large_dataset(self):
        """测试大数据集（超过宽度）"""
        values = list(range(1, 31))  # 30 个值
        result = _generate_ascii_chart(values, width=20)
        assert len(result) > 0
        # 应该分成多行显示
        lines = result.split("\n")
        assert len(lines) >= 2  # 至少 2 行


class TestFormatTrendOutput:
    """测试趋势输出格式化"""

    def test_empty_results(self):
        """测试空结果"""
        result = format_trend_output([])
        assert result == "无数据"

    def test_single_result(self):
        """测试单个结果"""
        indicators = SentimentIndicators(
            limit_up_count=100,
            broken_count=20,
            broken_rate=20.0,
            max_continuous=5,
            prev_avg_change=2.5,
            prev_profit_rate=60.0,
        )
        result_data = SentimentCycleResult(
            date="2026-03-11",
            cycle="高潮",
            indicators=indicators,
            reasons=["测试理由"],
            warnings=[],
        )
        output = format_trend_output([result_data])
        assert "情绪周期趋势分析" in output
        assert "2026-03-11" in output
        assert "高潮" in output

    def test_multiple_results(self):
        """测试多个结果"""
        results = []
        for i in range(5):
            indicators = SentimentIndicators(
                limit_up_count=50 + i * 10,
                broken_count=10 + i * 2,
                broken_rate=20.0 + i,
                max_continuous=3 + i,
                prev_avg_change=1.0 + i * 0.5,
                prev_profit_rate=50.0 + i * 5,
            )
            result_data = SentimentCycleResult(
                date=f"2026-03-{10 + i:02d}",
                cycle="加速",
                indicators=indicators,
                reasons=[],
                warnings=[],
            )
            results.append(result_data)

        output = format_trend_output(results)
        assert "情绪周期趋势分析" in output
        assert "涨停数趋势" in output
        assert "炸板率趋势" in output
        assert "周期统计" in output

    def test_results_with_warnings(self):
        """测试带警告的结果"""
        indicators = SentimentIndicators(
            limit_up_count=100,
            broken_count=0,
            broken_rate=0.0,  # 异常数据
            max_continuous=5,
            prev_avg_change=0.0,  # 异常数据
            prev_profit_rate=0.0,  # 异常数据
        )
        result_data = SentimentCycleResult(
            date="2026-03-11",
            cycle="分歧",
            indicators=indicators,
            reasons=["数据异常"],
            warnings=["炸板率为 0%", "昨日涨停表现数据缺失"],
        )
        output = format_trend_output([result_data])
        assert "⚠️  数据异常日期" in output
        assert "2026-03-11" in output
