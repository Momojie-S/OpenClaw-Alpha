# -*- coding: utf-8 -*-
"""SwIndustry Fetcher 测试"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from openclaw_alpha.core.data_source import DataSource
from openclaw_alpha.core.fetcher_registry import FetcherRegistry
from openclaw_alpha.core.registry import DataSourceRegistry
from openclaw_alpha.fetchers.sw_industry import (
    SwIndustryFetchParams,
    SwIndustryFetchResult,
    SwIndustryTushareFetcher,
)
from openclaw_alpha.fetchers.sw_industry.models import SwIndustryItem


class MockTushareDataSource(DataSource[str]):
    """测试用 Tushare 数据源"""

    @property
    def name(self) -> str:
        return "tushare"

    @property
    def required_config(self) -> list[str]:
        return []

    async def initialize(self) -> None:
        self._client = "tushare_client"


class TestSwIndustryFetchParams:
    """SwIndustryFetchParams 测试"""

    def test_default_params(self) -> None:
        """测试默认参数"""
        params = SwIndustryFetchParams()
        assert params.trade_date is None
        assert params.level == "L3"
        assert params.top == 50
        assert params.sort_by == "change_pct"

    def test_custom_params(self) -> None:
        """测试自定义参数"""
        params = SwIndustryFetchParams(
            trade_date="20260303",
            level="L1",
            top=20,
            sort_by="amount",
        )
        assert params.trade_date == "20260303"
        assert params.level == "L1"
        assert params.top == 20
        assert params.sort_by == "amount"


class TestSwIndustryItem:
    """SwIndustryItem 测试"""

    def test_item_creation(self) -> None:
        """测试创建数据项"""
        item = SwIndustryItem(
            rank=1,
            board_code="850001.SI",
            board_name="测试行业",
            change_pct=5.5,
            close=1000.0,
            volume=100.0,
            amount=10.0,
            turnover_rate=3.5,
            float_mv=1000.0,
            total_mv=2000.0,
            pe=15.0,
            pb=1.5,
        )

        assert item.rank == 1
        assert item.board_code == "850001.SI"
        assert item.board_name == "测试行业"


class TestSwIndustryTushareFetcher:
    """SwIndustryTushareFetcher 测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        FetcherRegistry.get_instance().reset()
        DataSourceRegistry.get_instance().reset()

    def test_fetcher_attributes(self) -> None:
        """测试 Fetcher 属性"""
        fetcher = SwIndustryTushareFetcher()
        assert fetcher.name == "tushare_sw_industry"
        assert fetcher.data_type == "sw_industry"
        assert fetcher.required_data_source == "tushare"
        assert fetcher.priority == 1

    def test_is_available_with_configured_data_source(self) -> None:
        """测试数据源已配置时可用"""
        ds_registry = DataSourceRegistry.get_instance()
        ds_registry.register(MockTushareDataSource)

        fetcher = SwIndustryTushareFetcher()
        assert fetcher.is_available() is True

    def test_is_available_without_data_source(self) -> None:
        """测试数据源未配置时不可用"""
        fetcher = SwIndustryTushareFetcher()
        assert fetcher.is_available() is False

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_fetch_with_mock_data(self) -> None:
        """测试获取数据（模拟）"""
        mock_df = pd.DataFrame({
            "ts_code": ["850001.SI", "850002.SI"],
            "name": ["行业A", "行业B"],
            "close": [1000.0, 2000.0],
            "pct_change": [5.5, 3.2],
            "vol": [100000, 200000],
            "amount": [1000000, 2000000],
            "float_mv": [10000000, 20000000],
            "total_mv": [20000000, 40000000],
            "pe": [15.0, 20.0],
            "pb": [1.5, 2.0],
        })

        mock_pro = MagicMock()
        mock_pro.sw_daily.return_value = mock_df

        with patch.dict("os.environ", {"TUSHARE_TOKEN": "test_token"}):
            with patch("tushare.pro_api", return_value=mock_pro):
                fetcher = SwIndustryTushareFetcher()
                params = SwIndustryFetchParams(trade_date="20260303", top=2)
                result = await fetcher.fetch(params)

                assert isinstance(result, SwIndustryFetchResult)
                assert result.data_source == "Tushare"
                assert result.trade_date == "20260303"
                assert len(result.items) == 2
                assert result.items[0].board_name == "行业A"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_fetch_empty_data(self) -> None:
        """测试获取空数据"""
        mock_pro = MagicMock()
        mock_pro.sw_daily.return_value = pd.DataFrame()

        with patch.dict("os.environ", {"TUSHARE_TOKEN": "test_token"}):
            with patch("tushare.pro_api", return_value=mock_pro):
                fetcher = SwIndustryTushareFetcher()
                params = SwIndustryFetchParams()
                result = await fetcher.fetch(params)

                assert isinstance(result, SwIndustryFetchResult)
                assert len(result.items) == 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_fetch_filter_by_level_l1(self) -> None:
        """测试按一级层级筛选"""
        mock_df = pd.DataFrame({
            "ts_code": ["801001.SI", "850001.SI"],  # L1 和 L3
            "name": ["一级行业", "三级行业"],
            "close": [1000.0, 500.0],
            "pct_change": [5.0, 3.0],
            "vol": [100000, 50000],
            "amount": [1000000, 500000],
            "float_mv": [10000000, 5000000],
            "total_mv": [20000000, 10000000],
            "pe": [15.0, 10.0],
            "pb": [1.5, 1.0],
        })

        mock_pro = MagicMock()
        mock_pro.sw_daily.return_value = mock_df

        with patch.dict("os.environ", {"TUSHARE_TOKEN": "test_token"}):
            with patch("tushare.pro_api", return_value=mock_pro):
                fetcher = SwIndustryTushareFetcher()
                params = SwIndustryFetchParams(level="L1")
                result = await fetcher.fetch(params)

                assert result.level == "L1"
                assert len(result.items) == 1
                assert result.items[0].board_name == "一级行业"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_fetch_without_token_raises_error(self) -> None:
        """测试未配置 Token 抛出异常"""
        fetcher = SwIndustryTushareFetcher()
        params = SwIndustryFetchParams()

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="TUSHARE_TOKEN 未配置"):
                await fetcher.fetch(params)

    def test_calculate_turnover_rate(self) -> None:
        """测试换手率计算"""
        fetcher = SwIndustryTushareFetcher()

        df = pd.DataFrame({
            "amount": [1000000],  # 千元
            "float_mv": [10000000],  # 万元
        })

        result = fetcher._calculate_turnover_rate(df)

        # 换手率 = (1000000 * 1000) / (10000000 * 10000) * 100 = 1.0
        assert result["turnover_rate"].iloc[0] == 1.0
