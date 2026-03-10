# -*- coding: utf-8 -*-
"""市场择时 Processor 测试"""

import pytest

from openclaw_alpha.skills.market_sentiment.timing_processor.timing_processor import (
    MarketTimingProcessor,
)


class TestMarketTimingProcessorNormalize:
    """测试标准化逻辑"""

    def test_normalize_value_middle(self):
        """测试中间值"""
        processor = MarketTimingProcessor()
        result = processor._normalize_value(50, 0, 100)
        assert result == 50

    def test_normalize_value_min(self):
        """测试最小值"""
        processor = MarketTimingProcessor()
        result = processor._normalize_value(0, 0, 100)
        assert result == 0

    def test_normalize_value_max(self):
        """测试最大值"""
        processor = MarketTimingProcessor()
        result = processor._normalize_value(100, 0, 100)
        assert result == 100

    def test_normalize_value_reverse(self):
        """测试反向标准化"""
        processor = MarketTimingProcessor()
        result = processor._normalize_value(0, 0, 100, reverse=True)
        assert result == 100

    def test_normalize_value_out_of_range_high(self):
        """测试超出范围高值"""
        processor = MarketTimingProcessor()
        result = processor._normalize_value(150, 0, 100)
        assert result == 100

    def test_normalize_value_out_of_range_low(self):
        """测试超出范围低值"""
        processor = MarketTimingProcessor()
        result = processor._normalize_value(-50, 0, 100)
        assert result == 0


class TestMarketTimingProcessorLimitScore:
    """测试涨跌停比得分计算"""

    def test_limit_ratio_equal(self):
        """测试涨跌停相等"""
        processor = MarketTimingProcessor()
        score = processor._calc_limit_ratio_score(50, 50)
        assert score == 50

    def test_limit_ratio_high(self):
        """测试涨停远多于跌停"""
        processor = MarketTimingProcessor()
        score = processor._calc_limit_ratio_score(100, 10)
        assert score > 75

    def test_limit_ratio_low(self):
        """测试跌停多于涨停"""
        processor = MarketTimingProcessor()
        score = processor._calc_limit_ratio_score(10, 50)
        assert score < 25

    def test_limit_ratio_no_down(self):
        """测试无跌停"""
        processor = MarketTimingProcessor()
        score = processor._calc_limit_ratio_score(100, 0)
        assert score == 50  # 涨停数/2

    def test_limit_ratio_very_high(self):
        """测试极多涨停"""
        processor = MarketTimingProcessor()
        score = processor._calc_limit_ratio_score(200, 5)
        assert score >= 90


class TestMarketTimingProcessorTrendScore:
    """测试涨跌家数比得分计算"""

    def test_trend_ratio_equal(self):
        """测试涨跌家数相等"""
        processor = MarketTimingProcessor()
        score = processor._calc_trend_ratio_score(2500, 2500)
        assert score == 50

    def test_trend_ratio_all_up(self):
        """测试全涨"""
        processor = MarketTimingProcessor()
        score = processor._calc_trend_ratio_score(5000, 0)
        assert score == 100

    def test_trend_ratio_all_down(self):
        """测试全跌"""
        processor = MarketTimingProcessor()
        score = processor._calc_trend_ratio_score(0, 5000)
        assert score == 0

    def test_trend_ratio_mostly_up(self):
        """测试多数上涨"""
        processor = MarketTimingProcessor()
        score = processor._calc_trend_ratio_score(3500, 1500)
        assert 60 < score < 80


class TestMarketTimingProcessorFlowScore:
    """测试资金流向得分计算"""

    def test_flow_neutral(self):
        """测试资金中性"""
        processor = MarketTimingProcessor()
        score = processor._calc_flow_score(0)
        assert score == 50

    def test_flow_large_inflow(self):
        """测试大幅流入"""
        processor = MarketTimingProcessor()
        score = processor._calc_flow_score(1.5)
        assert score > 80

    def test_flow_large_outflow(self):
        """测试大幅流出"""
        processor = MarketTimingProcessor()
        score = processor._calc_flow_score(-1.5)
        assert score < 20


class TestMarketTimingProcessorSentimentIndex:
    """测试情绪综合指数计算"""

    def test_sentiment_index_without_breadth(self):
        """测试无宽度数据时的情绪指数"""
        processor = MarketTimingProcessor()
        index = processor._calc_sentiment_index(
            temperature=50,
            limit_score=50,
            trend_score=50,
            flow_score=50,
            breadth_score=None,
        )
        assert index == 50

    def test_sentiment_index_with_breadth(self):
        """测试有宽度数据时的情绪指数"""
        processor = MarketTimingProcessor()
        index = processor._calc_sentiment_index(
            temperature=60,
            limit_score=70,
            trend_score=80,
            flow_score=60,
            breadth_score=70,
        )
        # 加权平均
        expected = 60 * 0.25 + 70 * 0.20 + 80 * 0.15 + 60 * 0.15 + 70 * 0.25
        assert abs(index - expected) < 0.1

    def test_sentiment_index_extreme_low(self):
        """测试极低情绪指数"""
        processor = MarketTimingProcessor()
        index = processor._calc_sentiment_index(
            temperature=10,
            limit_score=20,
            trend_score=15,
            flow_score=25,
            breadth_score=10,
        )
        assert index < 25


class TestMarketTimingProcessorZone:
    """测试情绪分区判断"""

    def test_zone_extreme_low(self):
        """测试极度低迷区"""
        processor = MarketTimingProcessor()
        zone = processor._determine_zone(15)
        assert zone == "极度低迷"

    def test_zone_low(self):
        """测试低迷区"""
        processor = MarketTimingProcessor()
        zone = processor._determine_zone(35)
        assert zone == "低迷"

    def test_zone_neutral(self):
        """测试中性区"""
        processor = MarketTimingProcessor()
        zone = processor._determine_zone(50)
        assert zone == "中性"

    def test_zone_high(self):
        """测试高涨区"""
        processor = MarketTimingProcessor()
        zone = processor._determine_zone(68)
        assert zone == "高涨"

    def test_zone_extreme_high(self):
        """测试极度高涨区"""
        processor = MarketTimingProcessor()
        zone = processor._determine_zone(85)
        assert zone == "极度高涨"


class TestMarketTimingProcessorLeftSignal:
    """测试左侧择时信号"""

    def test_left_signal_strong_buy(self):
        """测试强买入信号"""
        processor = MarketTimingProcessor()
        signal = processor._determine_left_signal(15)
        assert signal["signal"] == "强买入"

    def test_left_signal_buy(self):
        """测试买入信号"""
        processor = MarketTimingProcessor()
        signal = processor._determine_left_signal(25)
        assert signal["signal"] == "买入"

    def test_left_signal_hold(self):
        """测试持有信号"""
        processor = MarketTimingProcessor()
        signal = processor._determine_left_signal(50)
        assert signal["signal"] == "持有"

    def test_left_signal_sell(self):
        """测试卖出信号"""
        processor = MarketTimingProcessor()
        signal = processor._determine_left_signal(72)
        assert signal["signal"] == "卖出"

    def test_left_signal_strong_sell(self):
        """测试强卖出信号"""
        processor = MarketTimingProcessor()
        signal = processor._determine_left_signal(85)
        assert signal["signal"] == "强卖出"


class TestMarketTimingProcessorRightSignal:
    """测试右侧择时信号"""

    def test_right_signal_no_prev(self):
        """测试无前一日数据"""
        processor = MarketTimingProcessor()
        signal = processor._determine_right_signal(50, None)
        assert signal["signal"] == "等待"

    def test_right_signal_large_rise(self):
        """测试情绪大涨"""
        processor = MarketTimingProcessor()
        signal = processor._determine_right_signal(50, 40)  # +25%
        assert signal["signal"] == "买入"

    def test_right_signal_moderate_rise(self):
        """测试情绪小涨"""
        processor = MarketTimingProcessor()
        signal = processor._determine_right_signal(50, 45)  # +11%
        assert signal["signal"] == "偏多"

    def test_right_signal_large_fall(self):
        """测试情绪大跌"""
        processor = MarketTimingProcessor()
        signal = processor._determine_right_signal(40, 50)  # -20%
        assert signal["signal"] == "卖出"

    def test_right_signal_moderate_fall(self):
        """测试情绪小跌"""
        processor = MarketTimingProcessor()
        signal = processor._determine_right_signal(45, 50)  # -10%
        assert signal["signal"] == "偏空"

    def test_right_signal_hold(self):
        """测试情绪平稳"""
        processor = MarketTimingProcessor()
        signal = processor._determine_right_signal(51, 50)  # +2%
        assert signal["signal"] == "持有"


class TestMarketTimingProcessorRecommendation:
    """测试投资建议生成"""

    def test_recommendation_extreme_low(self):
        """测试极度低迷建议"""
        processor = MarketTimingProcessor()
        rec = processor._generate_recommendation(
            "极度低迷",
            {"signal": "强买入", "description": "test"},
            {"signal": "持有", "description": "test"},
            15,
        )
        assert "中长期布局良机" in rec

    def test_recommendation_extreme_high(self):
        """测试极度高涨建议"""
        processor = MarketTimingProcessor()
        rec = processor._generate_recommendation(
            "极度高涨",
            {"signal": "强卖出", "description": "test"},
            {"signal": "偏空", "description": "test"},
            85,
        )
        assert "降低仓位" in rec

    def test_recommendation_neutral(self):
        """测试中性建议"""
        processor = MarketTimingProcessor()
        rec = processor._generate_recommendation(
            "中性",
            {"signal": "持有", "description": "test"},
            {"signal": "持有", "description": "test"},
            50,
        )
        assert "中性" in rec
