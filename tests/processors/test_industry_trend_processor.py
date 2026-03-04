# -*- coding: utf-8 -*-
"""IndustryTrend Processor 测试"""

from unittest.mock import AsyncMock, patch

import pytest

from openclaw_alpha.core.data_source import DataSource
from openclaw_alpha.core.fetcher_registry import FetcherRegistry
from openclaw_alpha.core.registry import DataSourceRegistry
from openclaw_alpha.fetchers.concept_board import (
    ConceptBoardAkshareFetcher,
    ConceptBoardFetchParams,
    ConceptBoardFetchResult,
    ConceptBoardItem,
)
from openclaw_alpha.fetchers.sw_industry import (
    SwIndustryFetchParams,
    SwIndustryFetchResult,
    SwIndustryItem,
    SwIndustryTushareFetcher,
)
from openclaw_alpha.processors.industry_trend import (
    IndustryTrendProcessParams,
    IndustryTrendProcessResult,
    IndustryTrendProcessor,
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


class TestIndustryTrendProcessParams:
    """IndustryTrendProcessParams 测试"""

    def test_default_params(self) -> None:
        """测试默认参数"""
        params = IndustryTrendProcessParams()
        assert params.top == 20
        assert params.sort_by == "change_pct"

    def test_custom_params(self) -> None:
        """测试自定义参数"""
        params = IndustryTrendProcessParams(top=50, sort_by="amount")
        assert params.top == 50
        assert params.sort_by == "amount"


class TestIndustryTrendProcessor:
    """IndustryTrendProcessor 测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        FetcherRegistry.get_instance().reset()
        DataSourceRegistry.get_instance().reset()

    def test_processor_attributes(self) -> None:
        """测试 Processor 属性"""
        processor = IndustryTrendProcessor()
        assert processor.name == "industry_trend"
        assert processor.required_data_types == ["concept_board", "sw_industry"]

    def test_check_availability_all_available(self) -> None:
        """测试所有数据类型可用"""
        # 注册数据源
        ds_registry = DataSourceRegistry.get_instance()
        ds_registry.register(MockAkshareDataSource)
        ds_registry.register(MockTushareDataSource)

        # 注册 Fetcher
        registry = FetcherRegistry.get_instance()
        registry.register(ConceptBoardAkshareFetcher())
        registry.register(SwIndustryTushareFetcher())

        processor = IndustryTrendProcessor()
        is_available, unavailable = processor.check_availability()

        assert is_available is True
        assert unavailable == []

    def test_check_availability_partial_available(self) -> None:
        """测试部分数据类型不可用"""
        # 只注册 akshare 数据源
        ds_registry = DataSourceRegistry.get_instance()
        ds_registry.register(MockAkshareDataSource)

        # 只注册 concept_board Fetcher
        registry = FetcherRegistry.get_instance()
        registry.register(ConceptBoardAkshareFetcher())

        processor = IndustryTrendProcessor()
        is_available, unavailable = processor.check_availability()

        assert is_available is False
        assert "sw_industry" in unavailable

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_process(self) -> None:
        """测试 process 方法"""
        # 注册数据源
        ds_registry = DataSourceRegistry.get_instance()
        ds_registry.register(MockAkshareDataSource)
        ds_registry.register(MockTushareDataSource)

        # 创建 mock Fetcher
        concept_fetcher = ConceptBoardAkshareFetcher()
        sw_industry_fetcher = SwIndustryTushareFetcher()

        # Mock fetch 方法
        concept_result = ConceptBoardFetchResult(
            trade_date="2026-03-04",
            data_source="东方财富",
            items=[
                ConceptBoardItem(
                    rank=1,
                    board_code="BK0001",
                    board_name="人工智能",
                    price=100.0,
                    change_pct=5.5,
                    change=5.0,
                    volume=10000.0,
                    amount=100000000.0,  # 1亿
                    turnover_rate=3.5,
                    up_count=50,
                    down_count=10,
                    leader_name="领涨股",
                    leader_change=10.0,
                    total_mv=10000000000.0,
                )
            ],
        )

        sw_industry_result = SwIndustryFetchResult(
            trade_date="20260304",
            level="L3",
            data_source="Tushare",
            items=[
                SwIndustryItem(
                    rank=1,
                    board_code="850001.SI",
                    board_name="软件开发",
                    change_pct=3.2,
                    close=1000.0,
                    volume=100.0,
                    amount=10.0,  # 亿元
                    turnover_rate=2.5,
                    float_mv=1000.0,
                    total_mv=2000.0,
                    pe=15.0,
                    pb=1.5,
                )
            ],
        )

        # 注册 Fetcher
        registry = FetcherRegistry.get_instance()
        registry.register(concept_fetcher)
        registry.register(sw_industry_fetcher)

        # Mock fetch 方法
        with patch.object(
            concept_fetcher, "fetch", new_callable=AsyncMock, return_value=concept_result
        ):
            with patch.object(
                sw_industry_fetcher,
                "fetch",
                new_callable=AsyncMock,
                return_value=sw_industry_result,
            ):
                processor = IndustryTrendProcessor()
                params = IndustryTrendProcessParams(top=1)
                result = await processor.process(params)

                assert isinstance(result, IndustryTrendProcessResult)
                assert len(result.concept_boards) == 1
                assert len(result.sw_industries) == 1
                assert result.concept_boards[0].board_name == "人工智能"
                assert result.sw_industries[0].board_name == "软件开发"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_process_partial_data_graceful_degradation(self) -> None:
        """测试部分数据不可用时，优雅降级返回部分结果"""
        # 注册数据源
        ds_registry = DataSourceRegistry.get_instance()
        ds_registry.register(MockAkshareDataSource)

        # 创建 mock Fetcher
        concept_fetcher = ConceptBoardAkshareFetcher()

        # Mock fetch 方法
        concept_result = ConceptBoardFetchResult(
            trade_date="2026-03-04",
            data_source="东方财富",
            items=[
                ConceptBoardItem(
                    rank=1,
                    board_code="BK0001",
                    board_name="人工智能",
                    price=100.0,
                    change_pct=5.5,
                    change=5.0,
                    volume=10000.0,
                    amount=100000000.0,
                    turnover_rate=3.5,
                    up_count=50,
                    down_count=10,
                    leader_name="领涨股",
                    leader_change=10.0,
                    total_mv=10000000000.0,
                )
            ],
        )

        # 注册 Fetcher
        registry = FetcherRegistry.get_instance()
        registry.register(concept_fetcher)

        # Mock fetch 方法
        with patch.object(
            concept_fetcher, "fetch", new_callable=AsyncMock, return_value=concept_result
        ):
            processor = IndustryTrendProcessor()
            params = IndustryTrendProcessParams(top=1)

            # sw_industry 不可用时，仍然返回部分结果（concept_boards 有数据，sw_industries 为空）
            result = await processor.process(params)

            assert isinstance(result, IndustryTrendProcessResult)
            assert len(result.concept_boards) == 1
            assert len(result.sw_industries) == 0  # 没有注册 sw_industry Fetcher

    def test_format_trade_date(self) -> None:
        """测试交易日期格式化"""
        processor = IndustryTrendProcessor()

        # YYYYMMDD 格式
        assert processor._format_trade_date("20260304") == "2026-03-04"

        # 已经是 YYYY-MM-DD 格式
        assert processor._format_trade_date("2026-03-04") == "2026-03-04"
