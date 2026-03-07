# -*- coding: utf-8 -*-
"""龙虎榜 Fetcher 测试"""

import pytest
from skills.lhb_tracker.scripts.lhb_fetcher.akshare_lhb import LhbFetcherAkshare


class TestLhbFetcherAkshare:
    """测试 LhbFetcherAkshare"""

    def test_transform_daily_basic(self):
        """测试基本转换"""
        fetcher = LhbFetcherAkshare()

        raw_data = [{
            "代码": "000001",
            "名称": "平安银行",
            "上榜日": "2026-03-06",
            "收盘价": 10.5,
            "涨跌幅": 9.98,
            "上榜原因": "日涨幅偏离值达到7%的前5只证券",
            "龙虎榜买入额": 500000000,
            "龙虎榜卖出额": 300000000,
            "龙虎榜净买额": 200000000,
            "解读": "主力买入",
        }]

        result = fetcher._transform_daily(raw_data)

        assert len(result) == 1
        assert result[0]["code"] == "000001"
        assert result[0]["name"] == "平安银行"
        assert result[0]["date"] == "2026-03-06"
        assert result[0]["close"] == 10.5
        assert result[0]["change_pct"] == 9.98
        assert result[0]["buy_amount"] == 500000000
        assert result[0]["sell_amount"] == 300000000
        assert result[0]["net_buy"] == 200000000
        assert result[0]["reason"] == "日涨幅偏离值达到7%的前5只证券"

    def test_transform_daily_multiple(self):
        """测试多条数据转换"""
        fetcher = LhbFetcherAkshare()

        raw_data = [
            {
                "代码": "000001",
                "名称": "平安银行",
                "上榜日": "2026-03-06",
                "收盘价": 10.5,
                "涨跌幅": 9.98,
                "上榜原因": "涨停",
                "龙虎榜买入额": 500000000,
                "龙虎榜卖出额": 300000000,
                "龙虎榜净买额": 200000000,
                "解读": "主力买入",
            },
            {
                "代码": "000002",
                "名称": "万科A",
                "上榜日": "2026-03-06",
                "收盘价": 7.5,
                "涨跌幅": -5.0,
                "上榜原因": "跌停",
                "龙虎榜买入额": 100000000,
                "龙虎榜卖出额": 300000000,
                "龙虎榜净买额": -200000000,
                "解读": "主力卖出",
            },
        ]

        result = fetcher._transform_daily(raw_data)

        assert len(result) == 2
        assert result[0]["code"] == "000001"
        assert result[0]["net_buy"] == 200000000
        assert result[1]["code"] == "000002"
        assert result[1]["net_buy"] == -200000000

    def test_transform_daily_missing_fields(self):
        """测试缺失字段处理"""
        fetcher = LhbFetcherAkshare()

        raw_data = [{
            "代码": "000001",
            "名称": "平安银行",
            "上榜日": "2026-03-06",
            # 缺失收盘价、涨跌幅等
            "上榜原因": "涨停",
            "龙虎榜买入额": None,  # None 值
            "龙虎榜卖出额": "invalid",  # 无效值
            "龙虎榜净买额": 0,
        }]

        result = fetcher._transform_daily(raw_data)

        assert len(result) == 1
        assert result[0]["code"] == "000001"
        assert result[0]["buy_amount"] == 0.0  # None 转换为 0
        assert result[0]["sell_amount"] == 0.0  # invalid 转换为 0
        assert result[0]["net_buy"] == 0.0

    def test_safe_float(self):
        """测试安全浮点转换"""
        fetcher = LhbFetcherAkshare()

        assert fetcher._safe_float(100) == 100.0
        assert fetcher._safe_float(100.5) == 100.5
        assert fetcher._safe_float("100.5") == 100.5
        assert fetcher._safe_float(None) == 0.0
        assert fetcher._safe_float("invalid") == 0.0
        assert fetcher._safe_float(float("nan")) != fetcher._safe_float(float("nan"))  # nan != nan
