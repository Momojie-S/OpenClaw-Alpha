# -*- coding: utf-8 -*-
"""数据源注册表测试"""

import pytest

from openclaw_alpha.core.data_source import DataSource
from openclaw_alpha.core.exceptions import DuplicateDataSourceError
from openclaw_alpha.core.registry import DataSourceRegistry


class MockDataSource1(DataSource[str]):
    """测试用数据源 1"""

    def __init__(self) -> None:
        super().__init__()
        self._client = "client1"

    @property
    def name(self) -> str:
        return "mock1"

    @property
    def required_config(self) -> list[str]:
        return []

    async def initialize(self) -> None:
        self._client = "initialized_client1"


class MockDataSource2(DataSource[str]):
    """测试用数据源 2"""

    @property
    def name(self) -> str:
        return "mock2"

    @property
    def required_config(self) -> list[str]:
        return ["REQUIRED_KEY"]


class TestDataSourceRegistry:
    """DataSourceRegistry 测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        registry = DataSourceRegistry.get_instance()
        registry.reset()

    def test_singleton(self) -> None:
        """测试单例模式"""
        registry1 = DataSourceRegistry.get_instance()
        registry2 = DataSourceRegistry.get_instance()
        assert registry1 is registry2

    def test_register_and_get(self) -> None:
        """测试注册和获取"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockDataSource1)

        ds = registry.get("mock1")
        assert isinstance(ds, MockDataSource1)
        assert ds.name == "mock1"

    def test_register_duplicate_raises_error(self) -> None:
        """测试注册重名抛出异常"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockDataSource1)

        with pytest.raises(DuplicateDataSourceError):
            registry.register(MockDataSource1)

    def test_get_unregistered_raises_key_error(self) -> None:
        """测试获取未注册的数据源抛出 KeyError"""
        registry = DataSourceRegistry.get_instance()

        with pytest.raises(KeyError):
            registry.get("unknown")

    def test_get_returns_same_instance(self) -> None:
        """测试多次获取返回同一实例"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockDataSource1)

        ds1 = registry.get("mock1")
        ds2 = registry.get("mock1")
        assert ds1 is ds2

    def test_is_available_registered_and_available(self) -> None:
        """测试已注册且可用"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockDataSource1)

        assert registry.is_available("mock1") is True

    def test_is_available_unregistered(self) -> None:
        """测试未注册"""
        registry = DataSourceRegistry.get_instance()

        assert registry.is_available("unknown") is False

    def test_reset_clears_all(self) -> None:
        """测试 reset 清除所有"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockDataSource1)
        registry.get("mock1")

        registry.reset()

        with pytest.raises(KeyError):
            registry.get("mock1")

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_close_all(self) -> None:
        """测试关闭所有数据源"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockDataSource1)

        ds = registry.get("mock1")
        await ds.get_client()
        assert ds._initialized is True

        await registry.close_all()
        assert ds._initialized is False
