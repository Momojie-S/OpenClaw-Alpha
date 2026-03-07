# -*- coding: utf-8 -*-
"""涨跌停数据获取器测试"""

import pytest
import pandas as pd

from skills.market_sentiment.scripts.limit_fetcher.akshare_impl import LimitFetcherAkshare


class TestLimitFetcherTransform:
    """测试 LimitFetcherAkshare 的数据转换逻辑"""

    def test_transform_basic(self):
        """测试基本转换"""
        method = LimitFetcherAkshare()
        
        # 模拟 API 返回数据
        raw_data = {
            "date": "2026-03-06",
            "limit_up_df": pd.DataFrame({
                "代码": ["000001", "000002", "000003"],
                "名称": ["平安银行", "万科A", "国农科技"],
            }),
            "break_count": 5,
        }
        
        result = method._transform(raw_data)
        
        assert result["date"] == "2026-03-06"
        assert result["limit_up"] == 3
        assert result["limit_down"] == 0  # AKShare 没有跌停数据
        assert result["break_board"] == 5

    def test_transform_empty_limit_up(self):
        """测试涨停为空的情况"""
        method = LimitFetcherAkshare()
        
        raw_data = {
            "date": "2026-03-06",
            "limit_up_df": pd.DataFrame(),
            "break_count": 0,
        }
        
        result = method._transform(raw_data)
        
        assert result["date"] == "2026-03-06"
        assert result["limit_up"] == 0
        assert result["limit_down"] == 0
        assert result["break_board"] == 0

    def test_transform_many_limit_up(self):
        """测试涨停数量较多的情况"""
        method = LimitFetcherAkshare()
        
        # 模拟 50 只涨停股
        codes = [f"0000{i:03d}" for i in range(50)]
        raw_data = {
            "date": "2026-03-06",
            "limit_up_df": pd.DataFrame({
                "代码": codes,
                "名称": [f"股票{i}" for i in range(50)],
            }),
            "break_count": 20,
        }
        
        result = method._transform(raw_data)
        
        assert result["limit_up"] == 50
        assert result["break_board"] == 20

    def test_transform_with_break_board(self):
        """测试有炸板的情况"""
        method = LimitFetcherAkshare()
        
        raw_data = {
            "date": "2026-03-06",
            "limit_up_df": pd.DataFrame({
                "代码": ["000001", "000002"],
                "名称": ["平安银行", "万科A"],
            }),
            "break_count": 15,  # 炸板数量大于涨停数量
        }
        
        result = method._transform(raw_data)
        
        assert result["limit_up"] == 2
        assert result["break_board"] == 15
