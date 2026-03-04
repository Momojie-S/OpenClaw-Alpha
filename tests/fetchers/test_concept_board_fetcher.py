# -*- coding: utf-8 -*-
"""ConceptBoard Fetcher 测试"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from openclaw_alpha.core.data_source import DataSource
from openclaw_alpha.core.fetcher_registry import FetcherRegistry
from openclaw_alpha.core.registry import DataSourceRegistry
from openclaw_alpha.fetchers.concept_board import (
    ConceptBoardAkshareFetcher,
    ConceptBoardFetchParams,
    ConceptBoardFetchResult,
    ConceptBoardTushareFetcher,
)


class MockAkshareDataSource(DataSource[str]):
    """测试用 Akshare 数据源"""

    @property
    def name(self) -> str:
        return "akshare"

    @property
    def required_config(self) -> list[str]:
        return []

    async def initialize(self) -> None:
        self._client = "akshare_client"


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


class TestConceptBoardFetchParams:
    """ConceptBoardFetchParams 测试"""

    def test_default_params(self) -> None:
        """测试默认参数"""
        params = ConceptBoardFetchParams()
        assert params.top == 20
        assert params.sort_by == "change_pct"

    def test_custom_params(self) -> None:
        """测试自定义参数"""
        params = ConceptBoardFetchParams(top=50, sort_by="amount")
        assert params.top == 50
        assert params.sort_by == "amount"


class TestConceptBoardItem:
    """ConceptBoardItem 测试"""

    def test_item_creation(self) -> None:
        """测试创建数据项"""
        from openclaw_alpha.fetchers.concept_board.models import ConceptBoardItem

        item = ConceptBoardItem(
            rank=1,
            board_code="BK0001",
            board_name="测试板块",
            price=100.0,
            change_pct=5.5,
            change=5.0,
            volume=10000.0,
            amount=1000000.0,
            turnover_rate=3.5,
            up_count=50,
            down_count=10,
            leader_name="领涨股",
            leader_change=10.0,
            total_mv=10000000000.0,
        )

        assert item.rank == 1
        assert item.board_code == "BK0001"
        assert item.board_name == "测试板块"


class TestConceptBoardAkshareFetcher:
    """ConceptBoardAkshareFetcher 测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        FetcherRegistry.get_instance().reset()
        DataSourceRegistry.get_instance().reset()

    def test_fetcher_attributes(self) -> None:
        """测试 Fetcher 属性"""
        fetcher = ConceptBoardAkshareFetcher()
        assert fetcher.name == "akshare_concept"
        assert fetcher.data_type == "concept_board"
        assert fetcher.required_data_source == "akshare"
        assert fetcher.priority == 2

    def test_is_available_with_configured_data_source(self) -> None:
        """测试数据源已配置时可用"""
        ds_registry = DataSourceRegistry.get_instance()
        ds_registry.register(MockAkshareDataSource)

        fetcher = ConceptBoardAkshareFetcher()
        assert fetcher.is_available() is True

    def test_is_available_without_data_source(self) -> None:
        """测试数据源未配置时不可用"""
        fetcher = ConceptBoardAkshareFetcher()
        assert fetcher.is_available() is False

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_fetch_with_mock_data(self) -> None:
        """测试获取数据（模拟）"""
        # 模拟 AKShare 返回数据
        mock_df = pd.DataFrame({
            "板块代码": ["BK0001", "BK0002"],
            "板块名称": ["人工智能", "新能源"],
            "最新价": [100.0, 200.0],
            "涨跌幅": [5.5, 3.2],
            "涨跌额": [5.0, 6.0],
            "总成交量": [10000, 20000],
            "总成交额": [1000000, 2000000],
            "换手率": [3.5, 2.5],
            "上涨家数": [50, 40],
            "下跌家数": [10, 15],
            "领涨股票": ["股票A", "股票B"],
            "领涨股票_涨跌幅": [10.0, 8.0],
            "总市值": [10000000000, 20000000000],
        })

        with patch(
            "openclaw_alpha.fetchers.concept_board.akshare.ak.stock_board_concept_name_em",
            return_value=mock_df,
        ):
            fetcher = ConceptBoardAkshareFetcher()
            params = ConceptBoardFetchParams(top=2)
            result = await fetcher.fetch(params)

            assert isinstance(result, ConceptBoardFetchResult)
            assert result.data_source == "东方财富"
            assert len(result.items) == 2
            assert result.items[0].board_name == "人工智能"
            assert result.items[1].board_name == "新能源"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_fetch_empty_data(self) -> None:
        """测试获取空数据"""
        with patch(
            "openclaw_alpha.fetchers.concept_board.akshare.ak.stock_board_concept_name_em",
            return_value=pd.DataFrame(),
        ):
            fetcher = ConceptBoardAkshareFetcher()
            params = ConceptBoardFetchParams()
            result = await fetcher.fetch(params)

            assert isinstance(result, ConceptBoardFetchResult)
            assert len(result.items) == 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_fetch_sorted_by_change_pct(self) -> None:
        """测试按涨跌幅排序"""
        mock_df = pd.DataFrame({
            "板块代码": ["BK0001", "BK0002", "BK0003"],
            "板块名称": ["低涨幅", "高涨幅", "中涨幅"],
            "最新价": [100.0, 200.0, 150.0],
            "涨跌幅": [1.0, 10.0, 5.0],
            "涨跌额": [1.0, 20.0, 7.5],
            "总成交量": [10000, 30000, 20000],
            "总成交额": [1000000, 3000000, 2000000],
            "换手率": [1.0, 10.0, 5.0],
            "上涨家数": [10, 100, 50],
            "下跌家数": [5, 20, 10],
            "领涨股票": ["A", "B", "C"],
            "领涨股票_涨跌幅": [5.0, 15.0, 10.0],
            "总市值": [10000000000, 30000000000, 20000000000],
        })

        with patch(
            "openclaw_alpha.fetchers.concept_board.akshare.ak.stock_board_concept_name_em",
            return_value=mock_df,
        ):
            fetcher = ConceptBoardAkshareFetcher()
            params = ConceptBoardFetchParams(top=3, sort_by="change_pct")
            result = await fetcher.fetch(params)

            # 按涨跌幅降序排列
            assert result.items[0].board_name == "高涨幅"
            assert result.items[1].board_name == "中涨幅"
            assert result.items[2].board_name == "低涨幅"


class TestConceptBoardTushareFetcher:
    """ConceptBoardTushareFetcher 测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        FetcherRegistry.get_instance().reset()
        DataSourceRegistry.get_instance().reset()

    def test_fetcher_attributes(self) -> None:
        """测试 Fetcher 属性"""
        fetcher = ConceptBoardTushareFetcher()
        assert fetcher.name == "tushare_concept"
        assert fetcher.data_type == "concept_board"
        assert fetcher.required_data_source == "tushare"
        assert fetcher.priority == 1

    def test_is_available_with_configured_data_source(self) -> None:
        """测试数据源已配置时可用"""
        ds_registry = DataSourceRegistry.get_instance()
        ds_registry.register(MockTushareDataSource)

        fetcher = ConceptBoardTushareFetcher()
        assert fetcher.is_available() is True

    def test_is_available_without_data_source(self) -> None:
        """测试数据源未配置时不可用"""
        fetcher = ConceptBoardTushareFetcher()
        assert fetcher.is_available() is False

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_fetch_with_mock_data(self) -> None:
        """测试获取数据（模拟）"""
        mock_df = pd.DataFrame({
            "code": ["TS001", "TS002"],
            "name": ["概念A", "概念B"],
        })

        mock_pro = MagicMock()
        mock_pro.concept.return_value = mock_df

        with patch.dict("os.environ", {"TUSHARE_TOKEN": "test_token"}):
            with patch("tushare.pro_api", return_value=mock_pro):
                fetcher = ConceptBoardTushareFetcher()
                params = ConceptBoardFetchParams(top=2)
                result = await fetcher.fetch(params)

                assert isinstance(result, ConceptBoardFetchResult)
                assert result.data_source == "Tushare"
                assert len(result.items) == 2

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_fetch_without_token_raises_error(self) -> None:
        """测试未配置 Token 抛出异常"""
        fetcher = ConceptBoardTushareFetcher()
        params = ConceptBoardFetchParams()

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="TUSHARE_TOKEN 未配置"):
                await fetcher.fetch(params)
