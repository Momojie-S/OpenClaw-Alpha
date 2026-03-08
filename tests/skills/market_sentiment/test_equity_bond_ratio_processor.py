# -*- coding: utf-8 -*-
"""股债性价比 Processor 测试"""

import pytest

from skills.market_sentiment.scripts.equity_bond_ratio_processor.equity_bond_ratio_processor import (
    EquityBondRatioProcessor,
)


class TestEquityBondRatioProcessorCalc:
    """测试计算逻辑"""

    def test_calc_risk_premium(self):
        """测试风险溢价计算"""
        processor = EquityBondRatioProcessor()

        # PE=10，股票收益率=10%，国债收益率=2%
        # 风险溢价 = 10 - 2 = 8%
        rp = processor._calc_risk_premium(10, 2)
        assert rp == 8

    def test_calc_risk_premium_high_pe(self):
        """测试高 PE 时的风险溢价"""
        processor = EquityBondRatioProcessor()

        # PE=50，股票收益率=2%，国债收益率=2%
        # 风险溢价 = 2 - 2 = 0
        rp = processor._calc_risk_premium(50, 2)
        assert rp == 0

    def test_calc_risk_premium_negative(self):
        """测试负风险溢价（股息率低于国债）"""
        processor = EquityBondRatioProcessor()

        # PE=100，股票收益率=1%，国债收益率=2%
        # 风险溢价 = 1 - 2 = -1
        rp = processor._calc_risk_premium(100, 2)
        assert rp == -1


class TestEquityBondRatioProcessorPercentile:
    """测试分位数计算"""

    def test_calc_percentile_low(self):
        """测试低分位数"""
        processor = EquityBondRatioProcessor()

        # 当前值1，历史数据[1,2,3,4,5]
        percentile = processor._calc_percentile(1, [1, 2, 3, 4, 5])
        assert percentile == 20

    def test_calc_percentile_high(self):
        """测试高分位数"""
        processor = EquityBondRatioProcessor()

        # 当前值5，历史数据[1,2,3,4,5]
        percentile = processor._calc_percentile(5, [1, 2, 3, 4, 5])
        assert percentile == 100

    def test_calc_percentile_middle(self):
        """测试中间分位数"""
        processor = EquityBondRatioProcessor()

        # 当前值3，历史数据[1,2,3,4,5]
        percentile = processor._calc_percentile(3, [1, 2, 3, 4, 5])
        assert percentile == 60

    def test_calc_percentile_empty(self):
        """测试空历史数据"""
        processor = EquityBondRatioProcessor()

        percentile = processor._calc_percentile(5, [])
        assert percentile == 50


class TestEquityBondRatioProcessorSignal:
    """测试择时信号判断"""

    def test_signal_strong_buy(self):
        """测试强买入信号"""
        processor = EquityBondRatioProcessor()

        signal = processor._determine_signal(85)
        assert signal["signal"] == "强买入"

    def test_signal_buy(self):
        """测试买入信号"""
        processor = EquityBondRatioProcessor()

        signal = processor._determine_signal(65)
        assert signal["signal"] == "买入"

    def test_signal_hold(self):
        """测试持有信号"""
        processor = EquityBondRatioProcessor()

        signal = processor._determine_signal(50)
        assert signal["signal"] == "持有"

    def test_signal_sell(self):
        """测试卖出信号"""
        processor = EquityBondRatioProcessor()

        signal = processor._determine_signal(35)
        assert signal["signal"] == "卖出"

    def test_signal_strong_sell(self):
        """测试强卖出信号"""
        processor = EquityBondRatioProcessor()

        signal = processor._determine_signal(15)
        assert signal["signal"] == "强卖出"


class TestEquityBondRatioProcessorRecommendation:
    """测试投资建议生成"""

    def test_recommendation_high_premium(self):
        """测试高风险溢价建议"""
        processor = EquityBondRatioProcessor()

        rec = processor._generate_recommendation(
            6.0,
            80,
            {"signal": "买入", "description": "test"},
        )
        assert "增加股票仓位" in rec

    def test_recommendation_low_premium(self):
        """测试低风险溢价建议"""
        processor = EquityBondRatioProcessor()

        rec = processor._generate_recommendation(
            1.0,
            20,
            {"signal": "卖出", "description": "test"},
        )
        assert "降低股票仓位" in rec

    def test_recommendation_neutral(self):
        """测试中性建议"""
        processor = EquityBondRatioProcessor()

        rec = processor._generate_recommendation(
            3.0,
            50,
            {"signal": "持有", "description": "test"},
        )
        assert "保持" in rec
