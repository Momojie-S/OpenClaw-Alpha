# -*- coding: utf-8 -*-
"""DataSourceRegistry 测试"""

import pytest

from openclaw_alpha.core.data_source import DataSource
from openclaw_alpha.core.exceptions import (
    DuplicateDataSourceError,
    UnregisteredDataSourceError,
)
from openclaw_alpha.core.registry import DataSourceRegistry


@pytest.fixture(autouse=True)
def reset_registry():
    """每个测试前重置注册表"""
    registry = DataSourceRegistry.get_instance()
    registry.reset()
    yield
    registry.reset()


class MockTestDataSource(DataSource):
    """测试用数据源"""

    @property
    def name(self) -> str:
        return "test_ds"

    @property
    def required_config(self) -> list[str]:
        return ["TEST_TOKEN"]


class MockTestDataSourceAnother(DataSource):
    """另一个测试用数据源"""

    @property
    def name(self) -> str:
        return "test_ds_another"

    @property
    def required_config(self) -> list[str]:
        return []


class TestDataSourceRegistry:
    """DataSourceRegistry 测试类"""

    def test_singleton(self):
        """测试单例模式"""
        registry1 = DataSourceRegistry.get_instance()
        registry2 = DataSourceRegistry.get_instance()
        assert registry1 is registry2

    def test_register_and_get(self):
        """测试注册和获取数据源"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockTestDataSource)

        ds = registry.get("test_ds")
        assert isinstance(ds, MockTestDataSource)
        assert ds.name == "test_ds"

    def test_register_duplicate(self):
        """测试重复注册抛出异常"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockTestDataSource)

        with pytest.raises(DuplicateDataSourceError) as exc_info:
            registry.register(MockTestDataSource)

        assert "test_ds" in str(exc_info.value)

    def test_get_not_found(self):
        """测试获取未注册的数据源"""
        registry = DataSourceRegistry.get_instance()

        with pytest.raises(UnregisteredDataSourceError) as exc_info:
            registry.get("not_exist")

        assert "not_exist" in str(exc_info.value)

    def test_is_available_registered(self, monkeypatch):
        """测试已注册数据源的可用性检查"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockTestDataSource)

        # 设置环境变量
        monkeypatch.setenv("TEST_TOKEN", "test_value")
        assert registry.is_available("test_ds") is True

        # 删除环境变量
        monkeypatch.delenv("TEST_TOKEN")
        assert registry.is_available("test_ds") is False

    def test_is_available_not_registered(self):
        """测试未注册数据源的可用性检查"""
        registry = DataSourceRegistry.get_instance()
        assert registry.is_available("not_exist") is False

    def test_get_lazy_loading(self):
        """测试懒加载：多次 get 返回同一实例"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockTestDataSource)

        ds1 = registry.get("test_ds")
        ds2 = registry.get("test_ds")
        assert ds1 is ds2

    def test_reset(self):
        """测试重置注册表"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockTestDataSource)

        # 重置前可以获取
        ds = registry.get("test_ds")
        assert ds is not None

        # 重置
        registry.reset()

        # 重置后无法获取
        with pytest.raises(UnregisteredDataSourceError):
            registry.get("test_ds")

    def test_register_multiple(self):
        """测试注册多个数据源"""
        registry = DataSourceRegistry.get_instance()
        registry.register(MockTestDataSource)
        registry.register(MockTestDataSourceAnother)

        ds1 = registry.get("test_ds")
        ds2 = registry.get("test_ds_another")

        assert isinstance(ds1, MockTestDataSource)
        assert isinstance(ds2, MockTestDataSourceAnother)
