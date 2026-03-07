# -*- coding: utf-8 -*-
"""个股分析 Processor 测试"""

import pytest

from skills.stock_analysis.scripts.stock_analysis_processor.stock_analysis_processor import StockAnalysisProcessor


class TestStockAnalysisProcessorAnalyze:
    """测试分析逻辑"""

    def test_analyze_very_active(self):
        """测试非常活跃的判断"""
        processor = StockAnalysisProcessor()
        stock_data = {
            "volume": {"turnover_rate": 15.0},
            "price": {"pct_change": 3.0},
        }
        result = processor._analyze(stock_data)
        assert result["activity"] == "非常活跃"
        assert result["trend"] == "上涨"

    def test_analyze_active(self):
        """测试较活跃的判断"""
        processor = StockAnalysisProcessor()
        stock_data = {
            "volume": {"turnover_rate": 7.0},
            "price": {"pct_change": 1.0},
        }
        result = processor._analyze(stock_data)
        assert result["activity"] == "较活跃"
        assert result["trend"] == "持平"

    def test_analyze_normal(self):
        """测试正常的判断"""
        processor = StockAnalysisProcessor()
        stock_data = {
            "volume": {"turnover_rate": 3.0},
            "price": {"pct_change": 0.5},
        }
        result = processor._analyze(stock_data)
        assert result["activity"] == "正常"
        assert result["trend"] == "持平"

    def test_analyze_inactive(self):
        """测试不活跃的判断"""
        processor = StockAnalysisProcessor()
        stock_data = {
            "volume": {"turnover_rate": 1.0},
            "price": {"pct_change": 0.1},
        }
        result = processor._analyze(stock_data)
        assert result["activity"] == "不活跃"
        assert result["trend"] == "持平"

    def test_analyze_big_up(self):
        """测试大涨的判断"""
        processor = StockAnalysisProcessor()
        stock_data = {
            "volume": {"turnover_rate": 5.0},
            "price": {"pct_change": 6.0},
        }
        result = processor._analyze(stock_data)
        assert result["trend"] == "大涨"

    def test_analyze_up(self):
        """测试上涨的判断"""
        processor = StockAnalysisProcessor()
        stock_data = {
            "volume": {"turnover_rate": 5.0},
            "price": {"pct_change": 3.0},
        }
        result = processor._analyze(stock_data)
        assert result["trend"] == "上涨"

    def test_analyze_big_down(self):
        """测试大跌的判断"""
        processor = StockAnalysisProcessor()
        stock_data = {
            "volume": {"turnover_rate": 5.0},
            "price": {"pct_change": -6.0},
        }
        result = processor._analyze(stock_data)
        assert result["trend"] == "大跌"

    def test_analyze_down(self):
        """测试下跌的判断"""
        processor = StockAnalysisProcessor()
        stock_data = {
            "volume": {"turnover_rate": 5.0},
            "price": {"pct_change": -3.0},
        }
        result = processor._analyze(stock_data)
        assert result["trend"] == "下跌"

    def test_analyze_zero_turnover(self):
        """测试换手率为 0 的情况"""
        processor = StockAnalysisProcessor()
        stock_data = {
            "volume": {"turnover_rate": 0.0},
            "price": {"pct_change": 0.0},
        }
        result = processor._analyze(stock_data)
        assert result["activity"] == "不活跃"
        assert result["trend"] == "持平"
