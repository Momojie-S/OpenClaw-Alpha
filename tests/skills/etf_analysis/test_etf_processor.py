# -*- coding: utf-8 -*-
"""ETF Processor 测试"""

import pytest
from openclaw_alpha.skills.etf_analysis.etf_processor.etf_processor import (
    filter_spot,
    sort_spot,
)


class TestFilterSpot:
    """筛选功能测试"""

    @pytest.fixture
    def sample_etfs(self):
        """测试数据（使用 dict 格式，与 Fetcher 返回一致）"""
        return [
            {
                "code": "sz159915",
                "name": "创业板ETF",
                "price": 2.0,
                "change_pct": 3.5,
                "change": 0.07,
                "amount": 10.0,
                "volume": 5000000,
                "open": 1.95,
                "high": 2.05,
                "low": 1.94,
                "prev_close": 1.93,
            },
            {
                "code": "sz159919",
                "name": "沪深300ETF",
                "price": 4.5,
                "change_pct": -1.2,
                "change": -0.05,
                "amount": 50.0,
                "volume": 11000000,
                "open": 4.55,
                "high": 4.6,
                "low": 4.4,
                "prev_close": 4.55,
            },
            {
                "code": "sz159949",
                "name": "创业板50ETF",
                "price": 1.2,
                "change_pct": 0.5,
                "change": 0.006,
                "amount": 5.0,
                "volume": 4000000,
                "open": 1.19,
                "high": 1.21,
                "low": 1.18,
                "prev_close": 1.194,
            },
        ]

    def test_filter_by_change_min(self, sample_etfs):
        """按涨跌幅下限筛选"""
        result = filter_spot(sample_etfs, change_min=1.0)
        # sz159915: 3.5 > 1.0 ✓, sz159949: 0.5 < 1.0 ✗
        assert len(result) == 1
        assert result[0]["code"] == "sz159915"

    def test_filter_by_change_max(self, sample_etfs):
        """按涨跌幅上限筛选"""
        result = filter_spot(sample_etfs, change_max=0.0)
        assert len(result) == 1
        assert result[0]["code"] == "sz159919"

    def test_filter_by_change_range(self, sample_etfs):
        """按涨跌幅范围筛选"""
        result = filter_spot(sample_etfs, change_min=0.0, change_max=2.0)
        assert len(result) == 1
        assert result[0]["code"] == "sz159949"

    def test_filter_by_amount_min(self, sample_etfs):
        """按成交额下限筛选"""
        result = filter_spot(sample_etfs, amount_min=10.0)
        assert len(result) == 2
        codes = [e["code"] for e in result]
        assert "sz159915" in codes
        assert "sz159919" in codes

    def test_filter_by_keyword(self, sample_etfs):
        """按关键词筛选"""
        result = filter_spot(sample_etfs, keyword="创业板")
        assert len(result) == 2
        for etf in result:
            assert "创业板" in etf["name"]

    def test_filter_combined(self, sample_etfs):
        """组合筛选"""
        result = filter_spot(
            sample_etfs, change_min=0.0, amount_min=5.0, keyword="ETF"
        )
        assert len(result) == 2

    def test_filter_no_match(self, sample_etfs):
        """无匹配结果"""
        result = filter_spot(sample_etfs, keyword="不存在的ETF")
        assert len(result) == 0

    def test_filter_no_condition(self, sample_etfs):
        """无筛选条件"""
        result = filter_spot(sample_etfs)
        assert len(result) == 3


class TestSortSpot:
    """排序功能测试"""

    @pytest.fixture
    def sample_etfs(self):
        """测试数据"""
        return [
            {
                "code": "sz159915",
                "name": "创业板ETF",
                "price": 2.0,
                "change_pct": 3.5,
                "change": 0.07,
                "amount": 10.0,
                "volume": 5000000,
            },
            {
                "code": "sz159919",
                "name": "沪深300ETF",
                "price": 4.5,
                "change_pct": -1.2,
                "change": -0.05,
                "amount": 50.0,
                "volume": 11000000,
            },
            {
                "code": "sz159949",
                "name": "创业板50ETF",
                "price": 1.2,
                "change_pct": 0.5,
                "change": 0.006,
                "amount": 5.0,
                "volume": 4000000,
            },
        ]

    def test_sort_by_change(self, sample_etfs):
        """按涨跌幅排序"""
        result = sort_spot(sample_etfs, sort_by="change")
        assert result[0]["change_pct"] == 3.5
        assert result[1]["change_pct"] == 0.5
        assert result[2]["change_pct"] == -1.2

    def test_sort_by_amount(self, sample_etfs):
        """按成交额排序"""
        result = sort_spot(sample_etfs, sort_by="amount")
        assert result[0]["amount"] == 50.0
        assert result[1]["amount"] == 10.0
        assert result[2]["amount"] == 5.0

    def test_sort_by_price(self, sample_etfs):
        """按价格排序"""
        result = sort_spot(sample_etfs, sort_by="price")
        assert result[0]["price"] == 4.5
        assert result[1]["price"] == 2.0
        assert result[2]["price"] == 1.2

    def test_sort_invalid_field(self, sample_etfs):
        """无效排序字段（使用默认）"""
        result = sort_spot(sample_etfs, sort_by="invalid")
        # 默认按涨跌幅排序
        assert result[0]["change_pct"] == 3.5
