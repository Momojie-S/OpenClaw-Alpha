# -*- coding: utf-8 -*-
"""市场情绪分析 Processor 测试"""

import pytest

from skills.market_sentiment.scripts.sentiment_processor.sentiment_processor import (
    MarketSentimentProcessor,
)


class TestMarketSentimentProcessorTemperature:
    """测试市场温度计算逻辑"""

    def test_calculate_temperature_hot(self):
        """测试高温市场"""
        processor = MarketSentimentProcessor()
        
        limit_data = {"limit_up": 150, "limit_down": 5, "break_board": 20}
        trend_data = {"up": 3500, "down": 1000, "flat": 500, "total": 5000}
        flow_data = {"main_net_inflow": 1000000000, "main_net_inflow_pct": 1.5}
        
        temperature = processor._calculate_temperature(limit_data, trend_data, flow_data)
        
        # 涨停多、涨多跌少、主力流入大 -> 应该是高温
        assert temperature >= 70

    def test_calculate_temperature_cold(self):
        """测试低温市场"""
        processor = MarketSentimentProcessor()
        
        limit_data = {"limit_up": 10, "limit_down": 50, "break_board": 5}
        trend_data = {"up": 1000, "down": 3500, "flat": 500, "total": 5000}
        flow_data = {"main_net_inflow": -2000000000, "main_net_inflow_pct": -1.5}
        
        temperature = processor._calculate_temperature(limit_data, trend_data, flow_data)
        
        # 涨停少、跌多涨少、主力流出大 -> 应该是低温
        assert temperature <= 40

    def test_calculate_temperature_normal(self):
        """测试正常市场"""
        processor = MarketSentimentProcessor()
        
        limit_data = {"limit_up": 50, "limit_down": 10, "break_board": 10}
        trend_data = {"up": 2500, "down": 2000, "flat": 500, "total": 5000}
        flow_data = {"main_net_inflow": 100000000, "main_net_inflow_pct": 0.2}
        
        temperature = processor._calculate_temperature(limit_data, trend_data, flow_data)
        
        # 数据比较均衡 -> 应该在中间范围
        assert 30 <= temperature <= 70


class TestMarketSentimentProcessorStatus:
    """测试市场状态判断逻辑"""

    def test_determine_status_extremely_hot(self):
        """测试极度亢奋状态"""
        processor = MarketSentimentProcessor()
        
        status = processor._determine_status(90)
        assert status == "极度亢奋"

    def test_determine_status_hot(self):
        """测试偏热状态"""
        processor = MarketSentimentProcessor()
        
        status = processor._determine_status(70)
        assert status == "偏热"

    def test_determine_status_normal(self):
        """测试正常状态"""
        processor = MarketSentimentProcessor()
        
        status = processor._determine_status(50)
        assert status == "正常"

    def test_determine_status_cold(self):
        """测试偏冷状态"""
        processor = MarketSentimentProcessor()
        
        status = processor._determine_status(30)
        assert status == "偏冷"

    def test_determine_status_extremely_cold(self):
        """测试极度恐慌状态"""
        processor = MarketSentimentProcessor()
        
        status = processor._determine_status(10)
        assert status == "极度恐慌"


class TestMarketSentimentProcessorSignals:
    """测试极端信号识别逻辑"""

    def test_identify_signals_overheat(self):
        """测试过热预警信号"""
        processor = MarketSentimentProcessor()
        
        limit_data = {"limit_up": 250, "limit_down": 5, "break_board": 20}
        flow_data = {"main_net_inflow": 1000000000, "main_net_inflow_pct": 0.5}
        
        signals = processor._identify_signals(limit_data, flow_data, 92)
        
        assert "过热预警" in signals

    def test_identify_signals_panic_bottom(self):
        """测试恐慌底部信号"""
        processor = MarketSentimentProcessor()
        
        limit_data = {"limit_up": 5, "limit_down": 150, "break_board": 5}
        flow_data = {"main_net_inflow": -3000000000, "main_net_inflow_pct": -1.5}
        
        signals = processor._identify_signals(limit_data, flow_data, 8)
        
        assert "恐慌底部" in signals

    def test_identify_signals_main_outflow(self):
        """测试主力大幅流出信号"""
        processor = MarketSentimentProcessor()
        
        limit_data = {"limit_up": 50, "limit_down": 20, "break_board": 10}
        flow_data = {"main_net_inflow": -5000000000, "main_net_inflow_pct": -2.0}
        
        signals = processor._identify_signals(limit_data, flow_data, 40)
        
        assert "主力大幅流出" in signals

    def test_identify_signals_divergence(self):
        """测试分化严重信号"""
        processor = MarketSentimentProcessor()
        
        # 涨停多但跌停也不少
        limit_data = {"limit_up": 80, "limit_down": 30, "break_board": 25}
        flow_data = {"main_net_inflow": 100000000, "main_net_inflow_pct": 0.1}
        
        signals = processor._identify_signals(limit_data, flow_data, 55)
        
        assert "分化严重" in signals

    def test_identify_signals_no_signal(self):
        """测试无极端信号的情况"""
        processor = MarketSentimentProcessor()
        
        limit_data = {"limit_up": 30, "limit_down": 5, "break_board": 8}
        flow_data = {"main_net_inflow": 500000000, "main_net_inflow_pct": 0.3}
        
        signals = processor._identify_signals(limit_data, flow_data, 50)
        
        # 正常情况不应该有极端信号
        assert len(signals) == 0

    def test_identify_signals_multiple(self):
        """测试多个信号同时出现"""
        processor = MarketSentimentProcessor()
        
        # 过热 + 分化
        limit_data = {"limit_up": 220, "limit_down": 35, "break_board": 50}
        flow_data = {"main_net_inflow": -2000000000, "main_net_inflow_pct": -1.2}
        
        signals = processor._identify_signals(limit_data, flow_data, 85)
        
        # 应该有过热预警和分化严重
        assert "过热预警" in signals
        assert "分化严重" in signals
        assert "主力大幅流出" in signals
