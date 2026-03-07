# -*- coding: utf-8 -*-
"""资金流向数据获取器测试"""

import pytest

from skills.market_sentiment.scripts.flow_fetcher.akshare_impl import FlowFetcherAkshare


class TestFlowFetcherTransform:
    """测试 FlowFetcherAkshare 的数据转换逻辑"""

    def test_transform_basic(self):
        """测试基本转换"""
        method = FlowFetcherAkshare()
        
        raw_data = {
            "date": "2026-03-06",
            "main_net_inflow": 1000000000.0,  # 10亿
            "main_net_inflow_pct": 0.5,
            "retail_net_inflow": -500000000.0,  # -5亿
            "retail_net_inflow_pct": -0.3,
        }
        
        result = method._transform(raw_data)
        
        assert result["date"] == "2026-03-06"
        assert result["main_net_inflow"] == 1000000000.0
        assert result["main_net_inflow_pct"] == 0.5
        assert result["retail_net_inflow"] == -500000000.0
        assert result["retail_net_inflow_pct"] == -0.3

    def test_transform_main_outflow(self):
        """测试主力净流出的情况"""
        method = FlowFetcherAkshare()
        
        raw_data = {
            "date": "2026-03-06",
            "main_net_inflow": -2000000000.0,  # -20亿
            "main_net_inflow_pct": -1.2,
            "retail_net_inflow": 1000000000.0,  # 10亿
            "retail_net_inflow_pct": 0.6,
        }
        
        result = method._transform(raw_data)
        
        assert result["main_net_inflow"] == -2000000000.0
        assert result["main_net_inflow_pct"] == -1.2

    def test_transform_zero_flow(self):
        """测试零流量的情况"""
        method = FlowFetcherAkshare()
        
        raw_data = {
            "date": "2026-03-06",
            "main_net_inflow": 0.0,
            "main_net_inflow_pct": 0.0,
            "retail_net_inflow": 0.0,
            "retail_net_inflow_pct": 0.0,
        }
        
        result = method._transform(raw_data)
        
        assert result["main_net_inflow"] == 0.0
        assert result["main_net_inflow_pct"] == 0.0
