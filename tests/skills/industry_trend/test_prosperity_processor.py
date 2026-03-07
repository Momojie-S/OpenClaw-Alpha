# -*- coding: utf-8 -*-
"""行业景气度 Processor 测试"""

import pytest

from skills.industry_trend.scripts.prosperity_processor.prosperity_processor import (
    _calc_change,
    _judge_valuation_trend,
    _calc_prosperity_score,
    _judge_prosperity_level,
)


class TestCalcChange:
    """测试变化计算"""

    def test_calc_change_positive(self):
        """测试正向变化"""
        result = _calc_change(110, 100)
        assert result == 10.0

    def test_calc_change_negative(self):
        """测试负向变化"""
        result = _calc_change(90, 100)
        assert result == -10.0

    def test_calc_change_zero_previous(self):
        """测试前值为0"""
        result = _calc_change(100, 0)
        assert result is None

    def test_calc_change_none_current(self):
        """测试当前值为None"""
        result = _calc_change(None, 100)
        assert result is None

    def test_calc_change_none_previous(self):
        """测试前值为None"""
        result = _calc_change(100, None)
        assert result is None


class TestJudgeValuationTrend:
    """测试估值趋势判断"""

    def test_trend_up_both(self):
        """测试PE和PB都上升"""
        result = _judge_valuation_trend(10, 5)  # PE +10%, PB +5%
        assert result == "上升"

    def test_trend_down_both(self):
        """测试PE和PB都下降"""
        result = _judge_valuation_trend(-10, -5)  # PE -10%, PB -5%
        assert result == "下降"

    def test_trend_stable_pe_up_pb_stable(self):
        """测试PE上升PB稳定"""
        result = _judge_valuation_trend(10, 1)  # PE +10%, PB +1%（未超过3%）
        assert result == "稳定"

    def test_trend_stable_pe_stable_pb_up(self):
        """测试PE稳定PB上升"""
        result = _judge_valuation_trend(3, 5)  # PE +3%（未超过5%）, PB +5%
        assert result == "稳定"

    def test_trend_new_no_data(self):
        """测试无历史数据"""
        result = _judge_valuation_trend(None, None)
        assert result == "新"

    def test_trend_pe_only(self):
        """测试只有PE数据"""
        result = _judge_valuation_trend(10, None)  # PE +10%, PB无数据
        assert result == "稳定"  # PB默认稳定，综合为稳定

    def test_trend_pb_only(self):
        """测试只有PB数据"""
        result = _judge_valuation_trend(None, 5)  # PE无数据, PB +5%
        assert result == "稳定"  # PE默认稳定，综合为稳定


class TestCalcProsperityScore:
    """测试景气度评分计算"""

    def test_score_high_prosperity(self):
        """测试高景气"""
        # 估值上升（100分），涨跌幅 +10%（100分），市值 +10%（100分）
        score = _calc_prosperity_score("上升", 10, 10)
        assert score == 100.0

    def test_score_low_prosperity(self):
        """测试低景气"""
        # 估值下降（20分），涨跌幅 -10%（0分），市值 -10%（0分）
        score = _calc_prosperity_score("下降", -10, -10)
        assert score == 8.0  # 20*0.4 + 0*0.4 + 0*0.2 = 8

    def test_score_medium_prosperity(self):
        """测试中等景气"""
        # 估值稳定（60分），涨跌幅 0%（50分），市值 0%（50分）
        score = _calc_prosperity_score("稳定", 0, 0)
        assert score == 54.0  # 60*0.4 + 50*0.4 + 50*0.2 = 54

    def test_score_no_mv_data(self):
        """测试无市值数据"""
        # 估值上升（100分），涨跌幅 +5%（75分），市值无数据（50分）
        score = _calc_prosperity_score("上升", 5, None)
        expected = 100 * 0.4 + 75 * 0.4 + 50 * 0.2
        assert score == expected

    def test_score_new_trend(self):
        """测试新板块"""
        # 新板块（60分），涨跌幅 0%（50分），市值 0%（50分）
        score = _calc_prosperity_score("新", 0, 0)
        assert score == 54.0


class TestJudgeProsperityLevel:
    """测试景气度等级判断"""

    def test_level_high(self):
        """测试高景气"""
        assert _judge_prosperity_level(70) == "高景气"
        assert _judge_prosperity_level(80) == "高景气"
        assert _judge_prosperity_level(100) == "高景气"

    def test_level_medium(self):
        """测试中等景气"""
        assert _judge_prosperity_level(50) == "中等景气"
        assert _judge_prosperity_level(60) == "中等景气"
        assert _judge_prosperity_level(69.9) == "中等景气"

    def test_level_low(self):
        """测试低景气"""
        assert _judge_prosperity_level(49.9) == "低景气"
        assert _judge_prosperity_level(30) == "低景气"
        assert _judge_prosperity_level(0) == "低景气"
