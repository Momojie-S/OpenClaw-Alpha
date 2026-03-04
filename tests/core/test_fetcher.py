# -*- coding: utf-8 -*-
"""DataFetcher 基类测试"""

from dataclasses import dataclass

import pytest

from openclaw_alpha.core.data_source import DataSource
from openclaw_alpha.core.fetcher import DataFetcher
from openclaw_alpha.core.registry import DataSourceRegistry


@dataclass
class MockFetchParams:
    """测试用获取参数"""

    trade_date: str


@dataclass
class MockFetchResult:
    """测试用获取结果"""

    data: list[str]


class MockTushareDataSource(DataSource[str]):
    """测试用 Tushare 数据源"""

    def __init__(self, available: bool = True) -> None:
        super().__init__()
        self._available = available

    @property
    def name(self) -> str:
        return "tushare"

    @property
    def required_config(self) -> list[str]:
        return [] if self._available else ["MISSING_TOKEN"]

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


class TestFetcherAttributes:
    """DataFetcher 属性测试"""

    def test_name_attribute(self) -> None:
        """测试 name 属性"""
        fetcher = ConceptBoardTushareFetcher()
        assert fetcher.name == "tushare_concept"

    def test_data_type_attribute(self) -> None:
        """测试 data_type 属性"""
        fetcher = ConceptBoardTushareFetcher()
        assert fetcher.data_type == "concept_board"

    def test_required_data_source_attribute(self) -> None:
        """测试 required_data_source 属性"""
        fetcher = ConceptBoardTushareFetcher()
        assert fetcher.required_data_source == "tushare"

    def test_priority_attribute(self) -> None:
        """测试 priority 属性"""
        fetcher = ConceptBoardTushareFetcher()
        assert fetcher.priority == 1

        fetcher2 = ConceptBoardAkshareFetcher()
        assert fetcher2.priority == 2


class TestFetcherAvailability:
    """DataFetcher 可用性检查测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        registry = DataSourceRegistry.get_instance()
        registry.reset()

    def test_is_available_data_source_configured(self) -> None:
        """测试数据源已配置时返回 True"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockTushareDataSource)

        fetcher = ConceptBoardTushareFetcher()
        assert fetcher.is_available() is True

    def test_is_available_data_source_not_configured(self) -> None:
        """测试数据源未配置时返回 False"""
        # 不注册任何数据源
        DataSourceRegistry.get_instance()

        fetcher = ConceptBoardTushareFetcher()
        assert fetcher.is_available() is False

    def test_is_available_data_source_unavailable(self) -> None:
        """测试数据源配置不满足时返回 False"""
        registry = DataSourceRegistry.get_instance()
        registry.register(lambda: MockTushareDataSource(available=False))

        fetcher = ConceptBoardTushareFetcher()
        assert fetcher.is_available() is False


class TestFetcherGetClient:
    """DataFetcher get_client 测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        registry = DataSourceRegistry.get_instance()
        registry.reset()

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_client(self) -> None:
        """测试获取数据源客户端"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockTushareDataSource)

        client = await DataFetcher.get_client("tushare")
        assert client == "tushare_client"


class TestFetcherFetch:
    """DataFetcher fetch 测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        registry = DataSourceRegistry.get_instance()
        registry.reset()

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_fetch(self) -> None:
        """测试 fetch 方法"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockTushareDataSource)

        fetcher = ConceptBoardTushareFetcher()
        params = MockFetchParams(trade_date="20260303")
        result = await fetcher.fetch(params)

        assert result.data == ["concept1", "concept2"]

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_fetch_different_implementation(self) -> None:
        """测试不同实现返回不同结果"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockAkshareDataSource)

        fetcher = ConceptBoardAkshareFetcher()
        params = MockFetchParams(trade_date="20260303")
        result = await fetcher.fetch(params)

        assert result.data == ["concept3", "concept4"]
