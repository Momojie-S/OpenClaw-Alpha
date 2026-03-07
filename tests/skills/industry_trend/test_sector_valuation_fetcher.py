# -*- coding: utf-8 -*-
"""行业估值 Fetcher 测试"""

import pytest
from unittest.mock import patch, MagicMock

from skills.industry_trend.scripts.sector_valuation_fetcher.tushare import (
    SectorValuationFetcherTushare,
)


class TestSectorValuationFetcherTushare:
    """测试 SectorValuationFetcherTushare 转换逻辑"""

    @pytest.fixture
    def fetcher(self):
        """创建 Fetcher 实例"""
        return SectorValuationFetcherTushare()

    @pytest.fixture
    def mock_classifications(self):
        """模拟行业分类数据"""
        return [
            {"index_code": "801010.SI", "industry_name": "农林牧渔"},
            {"index_code": "801030.SI", "industry_name": "基础化工"},
            {"index_code": "801040.SI", "industry_name": "钢铁"},
        ]

    @pytest.fixture
    def mock_daily_data(self):
        """模拟日线行情数据"""
        return [
            {
                "ts_code": "801010.SI",
                "pe": 24.26,
                "pb": 2.66,
                "pct_change": 3.71,
                "float_mv": 69516298.0,
                "total_mv": 144804977.0,
            },
            {
                "ts_code": "801030.SI",
                "pe": 36.19,
                "pb": 2.68,
                "pct_change": 2.84,
                "float_mv": 252536858.0,
                "total_mv": 521187657.0,
            },
            {
                "ts_code": "801040.SI",
                "pe": None,  # 无 PE 数据
                "pb": 1.34,
                "pct_change": 0.34,
                "float_mv": 39819846.0,
                "total_mv": 113463833.0,
            },
        ]

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_extract_valuation_basic(self, fetcher, mock_classifications, mock_daily_data):
        """测试基本转换"""
        result = fetcher._extract_valuation(
            mock_classifications,
            mock_daily_data,
            "L1",
            "2026-03-06"
        )

        # 应该只有 2 条数据（钢铁无 PE，被跳过）
        assert len(result) == 2

        # 检查第一条数据
        first = result[0]
        assert first["name"] == "农林牧渔"
        assert first["code"] == "801010.SI"
        assert first["pe"] == 24.26
        assert first["pb"] == 2.66
        assert first["pct_change"] == 3.71

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_extract_valuation_skip_no_pe(self, fetcher, mock_classifications):
        """测试跳过无 PE 数据的板块"""
        daily_data = [
            {
                "ts_code": "801010.SI",
                "pe": None,  # 无 PE
                "pb": 2.66,
                "pct_change": 3.71,
                "float_mv": 69516298.0,
                "total_mv": 144804977.0,
            },
        ]

        result = fetcher._extract_valuation(
            mock_classifications,
            daily_data,
            "L1",
            "2026-03-06"
        )

        # 应该被跳过
        assert len(result) == 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_extract_valuation_skip_no_pb(self, fetcher, mock_classifications):
        """测试跳过无 PB 数据的板块"""
        daily_data = [
            {
                "ts_code": "801010.SI",
                "pe": 24.26,
                "pb": None,  # 无 PB
                "pct_change": 3.71,
                "float_mv": 69516298.0,
                "total_mv": 144804977.0,
            },
        ]

        result = fetcher._extract_valuation(
            mock_classifications,
            daily_data,
            "L1",
            "2026-03-06"
        )

        # 应该被跳过
        assert len(result) == 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_extract_valuation_empty_classifications(self, fetcher):
        """测试空分类数据"""
        result = fetcher._extract_valuation(
            [],
            [{"ts_code": "801010.SI", "pe": 24.26, "pb": 2.66, "pct_change": 3.71, "float_mv": 100, "total_mv": 200}],
            "L1",
            "2026-03-06"
        )

        assert len(result) == 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_extract_valuation_no_matching_daily(self, fetcher, mock_classifications):
        """测试日线数据无匹配"""
        result = fetcher._extract_valuation(
            mock_classifications,
            [{"ts_code": "999999.SI", "pe": 10, "pb": 1, "pct_change": 1, "float_mv": 100, "total_mv": 200}],  # 不存在的代码
            "L1",
            "2026-03-06"
        )

        assert len(result) == 0
