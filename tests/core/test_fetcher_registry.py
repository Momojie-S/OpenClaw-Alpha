# -*- coding: utf-8 -*-
"""FetcherRegistry 测试"""

from dataclasses import dataclass

import pytest

from openclaw_alpha.core.data_source import DataSource
from openclaw_alpha.core.exceptions import DuplicateFetcherError
from openclaw_alpha.core.fetcher import DataFetcher
from openclaw_alpha.core.fetcher_registry import FetcherRegistry
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
        return MockFetchResult(data=["concept1"])


class ConceptBoardAkshareFetcher(DataFetcher[MockFetchParams, MockFetchResult]):
    """测试用 Akshare 概念板块 Fetcher"""

    name = "akshare_concept"
    data_type = "concept_board"
    required_data_source = "akshare"
    priority = 2

    async def fetch(self, params: MockFetchParams) -> MockFetchResult:
        return MockFetchResult(data=["concept2"])


class SwIndustryTushareFetcher(DataFetcher[MockFetchParams, MockFetchResult]):
    """测试用 Tushare 申万行业 Fetcher"""

    name = "tushare_sw_industry"
    data_type = "sw_industry"
    required_data_source = "tushare"
    priority = 1

    async def fetch(self, params: MockFetchParams) -> MockFetchResult:
        return MockFetchResult(data=["industry1"])


class ConceptBoardLowPriorityFetcher(DataFetcher[MockFetchParams, MockFetchResult]):
    """测试用低优先级概念板块 Fetcher"""

    name = "low_priority_concept"
    data_type = "concept_board"
    required_data_source = "tushare"
    priority = 0

    async def fetch(self, params: MockFetchParams) -> MockFetchResult:
        return MockFetchResult(data=["concept3"])


class TestFetcherRegistrySingleton:
    """FetcherRegistry 单例测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        FetcherRegistry.get_instance().reset()

    def test_get_instance_returns_same_instance(self) -> None:
        """测试多次调用返回同一实例"""
        instance1 = FetcherRegistry.get_instance()
        instance2 = FetcherRegistry.get_instance()
        assert instance1 is instance2


class TestFetcherRegistryRegister:
    """FetcherRegistry 注册测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        FetcherRegistry.get_instance().reset()

    def test_register_success(self) -> None:
        """测试成功注册 Fetcher"""
        registry = FetcherRegistry.get_instance()
        fetcher = ConceptBoardTushareFetcher()
        registry.register(fetcher)

        # 验证可以通过名称获取
        result = registry.get("tushare_concept")
        assert result is fetcher

    def test_register_duplicate_name_raises_error(self) -> None:
        """测试注册重名 Fetcher 抛出异常"""
        registry = FetcherRegistry.get_instance()
        fetcher1 = ConceptBoardTushareFetcher()
        fetcher2 = ConceptBoardTushareFetcher()

        registry.register(fetcher1)

        with pytest.raises(DuplicateFetcherError) as exc_info:
            registry.register(fetcher2)

        assert exc_info.value.name == "tushare_concept"


class TestFetcherRegistryGet:
    """FetcherRegistry 获取测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        FetcherRegistry.get_instance().reset()

    def test_get_registered_fetcher(self) -> None:
        """测试获取已注册的 Fetcher"""
        registry = FetcherRegistry.get_instance()
        fetcher = ConceptBoardTushareFetcher()
        registry.register(fetcher)

        result = registry.get("tushare_concept")
        assert result is fetcher

    def test_get_unregistered_fetcher_raises_key_error(self) -> None:
        """测试获取未注册的 Fetcher 抛出 KeyError"""
        registry = FetcherRegistry.get_instance()

        with pytest.raises(KeyError) as exc_info:
            registry.get("unknown")

        assert "Fetcher 未注册" in str(exc_info.value)


class TestFetcherRegistryGetByDataType:
    """FetcherRegistry 按数据类型获取测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        FetcherRegistry.get_instance().reset()

    def test_get_by_data_type_returns_all(self) -> None:
        """测试获取同一类型的所有 Fetcher"""
        registry = FetcherRegistry.get_instance()
        fetcher1 = ConceptBoardTushareFetcher()
        fetcher2 = ConceptBoardAkshareFetcher()
        fetcher3 = SwIndustryTushareFetcher()

        registry.register(fetcher1)
        registry.register(fetcher2)
        registry.register(fetcher3)

        result = registry.get_by_data_type("concept_board")
        assert len(result) == 2
        assert fetcher1 in result
        assert fetcher2 in result

    def test_get_by_data_type_returns_empty_list_for_unknown(self) -> None:
        """测试获取不存在的类型返回空列表"""
        registry = FetcherRegistry.get_instance()

        result = registry.get_by_data_type("unknown_type")
        assert result == []


class TestFetcherRegistryGetAvailable:
    """FetcherRegistry 获取可用 Fetcher 测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        FetcherRegistry.get_instance().reset()
        DataSourceRegistry.get_instance().reset()

    def test_get_available_returns_available_fetchers(self) -> None:
        """测试获取可用的 Fetcher"""
        # 注册数据源
        ds_registry = DataSourceRegistry.get_instance()
        ds_registry.register(MockTushareDataSource)
        ds_registry.register(MockAkshareDataSource)

        # 注册 Fetcher
        registry = FetcherRegistry.get_instance()
        fetcher1 = ConceptBoardTushareFetcher()
        fetcher2 = ConceptBoardAkshareFetcher()
        registry.register(fetcher1)
        registry.register(fetcher2)

        result = registry.get_available("concept_board")
        assert len(result) == 2

    def test_get_available_sorted_by_priority(self) -> None:
        """测试按优先级降序排列"""
        # 注册数据源
        ds_registry = DataSourceRegistry.get_instance()
        ds_registry.register(MockTushareDataSource)

        # 注册 Fetcher（优先级：1 和 0）
        registry = FetcherRegistry.get_instance()
        fetcher1 = ConceptBoardTushareFetcher()  # priority=1
        fetcher2 = ConceptBoardLowPriorityFetcher()  # priority=0
        registry.register(fetcher1)
        registry.register(fetcher2)

        result = registry.get_available("concept_board")
        assert len(result) == 2
        # 高优先级在前
        assert result[0].priority == 1
        assert result[1].priority == 0

    def test_get_available_filters_unavailable(self) -> None:
        """测试过滤数据源不可用的 Fetcher"""
        # 只注册 akshare 数据源
        ds_registry = DataSourceRegistry.get_instance()
        ds_registry.register(MockAkshareDataSource)

        # 注册 Fetcher
        registry = FetcherRegistry.get_instance()
        fetcher1 = ConceptBoardTushareFetcher()  # 需要 tushare，不可用
        fetcher2 = ConceptBoardAkshareFetcher()  # 需要 akshare，可用
        registry.register(fetcher1)
        registry.register(fetcher2)

        result = registry.get_available("concept_board")
        assert len(result) == 1
        assert result[0].name == "akshare_concept"

    def test_get_available_returns_empty_list_when_all_unavailable(self) -> None:
        """测试所有 Fetcher 不可用时返回空列表"""
        # 不注册任何数据源

        registry = FetcherRegistry.get_instance()
        fetcher1 = ConceptBoardTushareFetcher()
        fetcher2 = ConceptBoardAkshareFetcher()
        registry.register(fetcher1)
        registry.register(fetcher2)

        result = registry.get_available("concept_board")
        assert result == []


class TestFetcherRegistryReset:
    """FetcherRegistry 重置测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        FetcherRegistry.get_instance().reset()

    def test_reset_clears_all_registrations(self) -> None:
        """测试重置清除所有注册"""
        registry = FetcherRegistry.get_instance()
        fetcher = ConceptBoardTushareFetcher()
        registry.register(fetcher)

        registry.reset()

        with pytest.raises(KeyError):
            registry.get("tushare_concept")
