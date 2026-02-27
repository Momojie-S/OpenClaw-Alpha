# -*- coding: utf-8 -*-
"""策略基类和入口测试"""

from dataclasses import dataclass

import pytest

from openclaw_alpha.core.data_source import DataSource
from openclaw_alpha.core.exceptions import NoAvailableImplementationError
from openclaw_alpha.core.registry import DataSourceRegistry
from openclaw_alpha.core.strategy import Strategy, StrategyEntry


@dataclass
class MockQuote:
    """测试用报价数据"""

    symbol: str
    price: float


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
        # available=True 时返回空列表（无需配置），False 时返回不存在的配置项
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


class StockQuoteTushare(Strategy[str, MockQuote]):
    """测试用 Tushare 策略实现"""

    _data_source_names = ["tushare"]

    async def run(self, symbol: str) -> MockQuote:
        return MockQuote(symbol=symbol, price=100.0)


class StockQuoteAkshare(Strategy[str, MockQuote]):
    """测试用 Akshare 策略实现"""

    _data_source_names = ["akshare"]

    async def run(self, symbol: str) -> MockQuote:
        return MockQuote(symbol=symbol, price=99.0)


class StockQuoteMultiSource(Strategy[str, MockQuote]):
    """测试用多数据源策略实现"""

    _data_source_names = ["tushare", "akshare"]

    async def run(self, symbol: str) -> MockQuote:
        return MockQuote(symbol=symbol, price=98.0)


class StockQuoteStrategy(StrategyEntry[str, MockQuote]):
    """测试用策略入口"""

    _data_source_names = []


class TestStrategy:
    """Strategy 测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        registry = DataSourceRegistry.get_instance()
        registry.reset()

    def test_data_source_names_class_attribute(self) -> None:
        """测试 _data_source_names 类属性"""
        assert StockQuoteTushare._data_source_names == ["tushare"]
        assert StockQuoteAkshare._data_source_names == ["akshare"]

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_client_static_method(self) -> None:
        """测试 get_client 静态方法"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockAkshareDataSource)

        client = await Strategy.get_client("akshare")
        assert client == "akshare_client"


class TestStrategyEntry:
    """StrategyEntry 测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        registry = DataSourceRegistry.get_instance()
        registry.reset()

    def test_register(self) -> None:
        """测试注册实现"""
        entry = StockQuoteStrategy()
        entry.register(StockQuoteTushare(), priority=1)
        entry.register(StockQuoteAkshare(), priority=2)

        assert len(entry._implementations) == 2

    def test_select_implementation_by_priority(self) -> None:
        """测试按优先级选择实现"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockAkshareDataSource)
        registry.register(MockTushareDataSource)

        entry = StockQuoteStrategy()
        entry.register(StockQuoteTushare(), priority=1)
        entry.register(StockQuoteAkshare(), priority=2)

        impl = entry._select_implementation()
        assert isinstance(impl, StockQuoteAkshare)

    def test_select_implementation_skip_unavailable(self) -> None:
        """测试跳过不可用的实现"""
        registry = DataSourceRegistry.get_instance()
        # 只注册 akshare，tushare 不可用
        registry.register(MockAkshareDataSource)

        entry = StockQuoteStrategy()
        entry.register(StockQuoteTushare(), priority=2)  # 高优先级但不可用
        entry.register(StockQuoteAkshare(), priority=1)

        impl = entry._select_implementation()
        assert isinstance(impl, StockQuoteAkshare)

    def test_select_implementation_all_unavailable(self) -> None:
        """测试所有实现不可用抛出异常"""
        DataSourceRegistry.get_instance()
        # 不注册任何数据源

        entry = StockQuoteStrategy()
        entry.register(StockQuoteTushare(), priority=1)
        entry.register(StockQuoteAkshare(), priority=2)

        with pytest.raises(NoAvailableImplementationError) as exc_info:
            entry._select_implementation()

        assert exc_info.value.strategy_name == "StockQuoteStrategy"

    def test_multi_source_all_available(self) -> None:
        """测试多数据源全部可用时选择优先级最高的"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockAkshareDataSource)
        registry.register(MockTushareDataSource)

        entry = StockQuoteStrategy()
        entry.register(StockQuoteMultiSource(), priority=3)  # 最高优先级
        entry.register(StockQuoteAkshare(), priority=2)

        impl = entry._select_implementation()
        assert isinstance(impl, StockQuoteMultiSource)

    def test_multi_source_partial_available(self) -> None:
        """测试多数据源部分可用时跳过"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockAkshareDataSource)
        # tushare 不可用

        entry = StockQuoteStrategy()
        entry.register(StockQuoteMultiSource(), priority=1)
        entry.register(StockQuoteAkshare(), priority=2)

        impl = entry._select_implementation()
        assert isinstance(impl, StockQuoteAkshare)

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_run(self) -> None:
        """测试运行策略"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockAkshareDataSource)

        entry = StockQuoteStrategy()
        entry.register(StockQuoteAkshare())

        result = await entry.run("000001")
        assert result.symbol == "000001"
        assert result.price == 99.0

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_run_selects_available_implementation(self) -> None:
        """测试运行时选择可用实现"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockAkshareDataSource)
        # tushare 不可用

        entry = StockQuoteStrategy()
        entry.register(StockQuoteTushare(), priority=2)
        entry.register(StockQuoteAkshare(), priority=1)

        result = await entry.run("000001")
        # 应该选择 akshare 实现
        assert result.price == 99.0
