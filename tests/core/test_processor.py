# -*- coding: utf-8 -*-
"""DataProcessor 基类测试"""

from dataclasses import dataclass

import pytest

from openclaw_alpha.core.data_source import DataSource
from openclaw_alpha.core.exceptions import NoAvailableFetcherError
from openclaw_alpha.core.fetcher import DataFetcher
from openclaw_alpha.core.fetcher_registry import FetcherRegistry
from openclaw_alpha.core.processor import DataProcessor
from openclaw_alpha.core.registry import DataSourceRegistry


@dataclass
class MockFetchParams:
    """测试用获取参数"""

    trade_date: str


@dataclass
class MockFetchResult:
    """测试用获取结果"""

    data: list[str]


@dataclass
class MockProcessParams:
    """测试用加工参数"""

    trade_date: str


@dataclass
class MockProcessResult:
    """测试用加工结果"""

    combined_data: list[str]


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


class ConceptBoardTushareFetcher(DataFetcher[MockFetchParams, MockFetchResult]):
    """测试用 Tushare 概念板块 Fetcher"""

    name = "tushare_concept"
    data_type = "concept_board"
    required_data_source = "tushare"
    priority = 1

    async def fetch(self, params: MockFetchParams) -> MockFetchResult:
        return MockFetchResult(data=["concept1", "concept2"])


class ConceptBoardAkshareFetcher(DataFetcher[MockFetchParams, MockFetchResult]):
    """测试用 Akshare 概念板块 Fetcher"""

    name = "akshare_concept"
    data_type = "concept_board"
    required_data_source = "akshare"
    priority = 2

    async def fetch(self, params: MockFetchParams) -> MockFetchResult:
        return MockFetchResult(data=["concept3", "concept4"])


class SwIndustryTushareFetcher(DataFetcher[MockFetchParams, MockFetchResult]):
    """测试用 Tushare 申万行业 Fetcher"""

    name = "tushare_sw_industry"
    data_type = "sw_industry"
    required_data_source = "tushare"
    priority = 1

    async def fetch(self, params: MockFetchParams) -> MockFetchResult:
        return MockFetchResult(data=["industry1", "industry2"])


class IndustryTrendProcessor(DataProcessor[MockProcessParams, MockProcessResult]):
    """测试用产业趋势 Processor"""

    name = "industry_trend"
    required_data_types = ["concept_board", "sw_industry"]

    async def process(self, params: MockProcessParams) -> MockProcessResult:
        # 获取 concept_board 数据
        concept_fetcher = self.get_available_fetcher("concept_board")
        concept_data = await concept_fetcher.fetch(MockFetchParams(trade_date=params.trade_date))

        # 获取 sw_industry 数据
        industry_fetcher = self.get_available_fetcher("sw_industry")
        industry_data = await industry_fetcher.fetch(MockFetchParams(trade_date=params.trade_date))

        # 组合数据
        return MockProcessResult(
            combined_data=concept_data.data + industry_data.data
        )


class SingleTypeProcessor(DataProcessor[MockProcessParams, MockProcessResult]):
    """测试用单类型 Processor"""

    name = "single_type"
    required_data_types = ["concept_board"]

    async def process(self, params: MockProcessParams) -> MockProcessResult:
        fetcher = self.get_available_fetcher("concept_board")
        data = await fetcher.fetch(MockFetchParams(trade_date=params.trade_date))
        return MockProcessResult(combined_data=data.data)


class TestProcessorAttributes:
    """DataProcessor 属性测试"""

    def test_name_attribute(self) -> None:
        """测试 name 属性"""
        processor = IndustryTrendProcessor()
        assert processor.name == "industry_trend"

    def test_required_data_types_attribute(self) -> None:
        """测试 required_data_types 属性"""
        processor = IndustryTrendProcessor()
        assert processor.required_data_types == ["concept_board", "sw_industry"]


class TestProcessorGetAvailableFetcher:
    """DataProcessor 获取可用 Fetcher 测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        FetcherRegistry.get_instance().reset()
        DataSourceRegistry.get_instance().reset()

    def test_get_available_fetcher_returns_highest_priority(self) -> None:
        """测试获取优先级最高的 Fetcher"""
        # 注册数据源
        ds_registry = DataSourceRegistry.get_instance()
        ds_registry.register(MockTushareDataSource)
        ds_registry.register(MockAkshareDataSource)

        # 注册 Fetcher
        registry = FetcherRegistry.get_instance()
        registry.register(ConceptBoardTushareFetcher())  # priority=1
        registry.register(ConceptBoardAkshareFetcher())  # priority=2

        processor = IndustryTrendProcessor()
        fetcher = processor.get_available_fetcher("concept_board")

        # akshare 优先级更高
        assert fetcher.name == "akshare_concept"

    def test_get_available_fetcher_raises_error_when_unavailable(self) -> None:
        """测试无可用 Fetcher 抛出异常"""
        # 不注册任何数据源和 Fetcher

        processor = IndustryTrendProcessor()

        with pytest.raises(NoAvailableFetcherError) as exc_info:
            processor.get_available_fetcher("concept_board")

        assert exc_info.value.data_type == "concept_board"

    def test_get_available_fetcher_filters_unavailable(self) -> None:
        """测试过滤数据源不可用的 Fetcher"""
        # 只注册 akshare 数据源
        ds_registry = DataSourceRegistry.get_instance()
        ds_registry.register(MockAkshareDataSource)

        # 注册 Fetcher
        registry = FetcherRegistry.get_instance()
        registry.register(ConceptBoardTushareFetcher())  # 需要 tushare，不可用
        registry.register(ConceptBoardAkshareFetcher())  # 需要 akshare，可用

        processor = IndustryTrendProcessor()
        fetcher = processor.get_available_fetcher("concept_board")

        assert fetcher.name == "akshare_concept"


class TestProcessorGetAllAvailableFetchers:
    """DataProcessor 获取所有可用 Fetcher 测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        FetcherRegistry.get_instance().reset()
        DataSourceRegistry.get_instance().reset()

    def test_get_all_available_fetchers(self) -> None:
        """测试获取所有可用 Fetcher"""
        # 注册数据源
        ds_registry = DataSourceRegistry.get_instance()
        ds_registry.register(MockTushareDataSource)
        ds_registry.register(MockAkshareDataSource)

        # 注册 Fetcher
        registry = FetcherRegistry.get_instance()
        registry.register(ConceptBoardTushareFetcher())
        registry.register(ConceptBoardAkshareFetcher())

        processor = IndustryTrendProcessor()
        fetchers = processor.get_all_available_fetchers("concept_board")

        assert len(fetchers) == 2

    def test_get_all_available_fetchers_returns_empty_when_unavailable(self) -> None:
        """测试无可用 Fetcher 返回空列表"""
        # 不注册任何数据源和 Fetcher

        processor = IndustryTrendProcessor()
        fetchers = processor.get_all_available_fetchers("concept_board")

        assert fetchers == []


class TestProcessorCheckAvailability:
    """DataProcessor 可用性检查测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        FetcherRegistry.get_instance().reset()
        DataSourceRegistry.get_instance().reset()

    def test_check_availability_all_available(self) -> None:
        """测试所有 data_type 可用"""
        # 注册数据源
        ds_registry = DataSourceRegistry.get_instance()
        ds_registry.register(MockTushareDataSource)

        # 注册 Fetcher
        registry = FetcherRegistry.get_instance()
        registry.register(ConceptBoardTushareFetcher())
        registry.register(SwIndustryTushareFetcher())

        processor = IndustryTrendProcessor()
        is_available, unavailable = processor.check_availability()

        assert is_available is True
        assert unavailable == []

    def test_check_availability_partial_available(self) -> None:
        """测试部分 data_type 不可用"""
        # 注册数据源
        ds_registry = DataSourceRegistry.get_instance()
        ds_registry.register(MockTushareDataSource)

        # 只注册 concept_board Fetcher
        registry = FetcherRegistry.get_instance()
        registry.register(ConceptBoardTushareFetcher())
        # 不注册 sw_industry Fetcher

        processor = IndustryTrendProcessor()
        is_available, unavailable = processor.check_availability()

        assert is_available is False
        assert "sw_industry" in unavailable

    def test_check_availability_none_available(self) -> None:
        """测试所有 data_type 不可用"""
        # 不注册任何数据源和 Fetcher

        processor = IndustryTrendProcessor()
        is_available, unavailable = processor.check_availability()

        assert is_available is False
        assert set(unavailable) == {"concept_board", "sw_industry"}


class TestProcessorProcess:
    """DataProcessor process 测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        FetcherRegistry.get_instance().reset()
        DataSourceRegistry.get_instance().reset()

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_process(self) -> None:
        """测试 process 方法"""
        # 注册数据源
        ds_registry = DataSourceRegistry.get_instance()
        ds_registry.register(MockTushareDataSource)

        # 注册 Fetcher
        registry = FetcherRegistry.get_instance()
        registry.register(ConceptBoardTushareFetcher())
        registry.register(SwIndustryTushareFetcher())

        processor = IndustryTrendProcessor()
        params = MockProcessParams(trade_date="20260303")
        result = await processor.process(params)

        assert result.combined_data == ["concept1", "concept2", "industry1", "industry2"]

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_process_single_type(self) -> None:
        """测试单类型 Processor"""
        # 注册数据源
        ds_registry = DataSourceRegistry.get_instance()
        ds_registry.register(MockTushareDataSource)

        # 注册 Fetcher
        registry = FetcherRegistry.get_instance()
        registry.register(ConceptBoardTushareFetcher())

        processor = SingleTypeProcessor()
        params = MockProcessParams(trade_date="20260303")
        result = await processor.process(params)

        assert result.combined_data == ["concept1", "concept2"]

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_process_raises_error_when_fetcher_unavailable(self) -> None:
        """测试无可用 Fetcher 时抛出异常"""
        # 不注册任何数据源和 Fetcher

        processor = IndustryTrendProcessor()
        params = MockProcessParams(trade_date="20260303")

        with pytest.raises(NoAvailableFetcherError):
            await processor.process(params)
