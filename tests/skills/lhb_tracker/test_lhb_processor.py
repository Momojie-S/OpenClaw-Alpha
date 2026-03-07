# -*- coding: utf-8 -*-
"""龙虎榜 Processor 测试"""

import pytest
from skills.lhb_tracker.scripts.lhb_processor.lhb_processor import analyze_buyer_type


class TestLhbProcessor:
    """测试 LhbProcessor"""

    def test_analyze_buyer_type_large(self):
        """测试大额净买入分类"""
        stock = {"net_buy": 150000000}  # 1.5亿
        result = analyze_buyer_type(stock)
        assert result == "机构+游资"

    def test_analyze_buyer_type_medium(self):
        """测试中等净买入分类"""
        stock = {"net_buy": 50000000}  # 0.5亿
        result = analyze_buyer_type(stock)
        assert result == "游资"

    def test_analyze_buyer_type_small(self):
        """测试小额净买入分类"""
        stock = {"net_buy": 10000000}  # 0.1亿
        result = analyze_buyer_type(stock)
        assert result == "游资"

    def test_analyze_buyer_type_outflow(self):
        """测试净卖出分类"""
        stock = {"net_buy": -50000000}  # -0.5亿
        result = analyze_buyer_type(stock)
        assert result == "卖盘为主"

    def test_analyze_buyer_type_zero(self):
        """测试零净买入分类"""
        stock = {"net_buy": 0}
        result = analyze_buyer_type(stock)
        assert result == "卖盘为主"

    def test_analyze_buyer_type_missing(self):
        """测试缺失净买入字段"""
        stock = {}
        result = analyze_buyer_type(stock)
        assert result == "卖盘为主"
