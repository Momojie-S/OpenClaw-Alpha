# -*- coding: utf-8 -*-
"""数据源基类测试"""

import os
from unittest.mock import patch

import pytest

from openclaw_alpha.core.data_source import DataSource


class MockDataSource(DataSource[str]):
    """测试用数据源"""

    def __init__(
        self, name: str = "mock", required_config: list[str] | None = None
    ) -> None:
        super().__init__()
        self._name = name
        self._required_config = required_config or []

    @property
    def name(self) -> str:
        return self._name

    @property
    def required_config(self) -> list[str]:
        return self._required_config

    async def initialize(self) -> None:
        self._client = "mock_client"

    async def close(self) -> None:
        await super().close()


class TestDataSource:
    """DataSource 测试"""

    def test_name_property(self) -> None:
        """测试 name 属性"""
        ds = MockDataSource(name="test_ds")
        assert ds.name == "test_ds"

    def test_required_config_property(self) -> None:
        """测试 required_config 属性"""
        ds = MockDataSource(required_config=["API_KEY", "API_SECRET"])
        assert ds.required_config == ["API_KEY", "API_SECRET"]

    def test_is_available_no_config_required(self) -> None:
        """测试无配置要求时始终可用"""
        ds = MockDataSource(required_config=[])
        assert ds.is_available() is True

    def test_is_available_all_config_set(self) -> None:
        """测试所有配置都已设置"""
        with patch.dict(os.environ, {"TEST_KEY": "test_value"}):
            ds = MockDataSource(required_config=["TEST_KEY"])
            assert ds.is_available() is True

    def test_is_available_missing_config(self) -> None:
        """测试缺少配置"""
        # 确保环境变量不存在
        os.environ.pop("MISSING_KEY", None)
        ds = MockDataSource(required_config=["MISSING_KEY"])
        assert ds.is_available() is False

    def test_is_available_empty_value(self) -> None:
        """测试配置值为空字符串"""
        with patch.dict(os.environ, {"EMPTY_KEY": ""}):
            ds = MockDataSource(required_config=["EMPTY_KEY"])
            assert ds.is_available() is False

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_client_lazy_initialization(self) -> None:
        """测试懒加载初始化"""
        ds = MockDataSource()
        assert ds._initialized is False
        assert ds._client is None

        client = await ds.get_client()
        assert ds._initialized is True
        assert client == "mock_client"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_client_returns_same_instance(self) -> None:
        """测试多次获取返回同一实例"""
        ds = MockDataSource()
        client1 = await ds.get_client()
        client2 = await ds.get_client()
        assert client1 is client2

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_close_resets_state(self) -> None:
        """测试 close 重置状态"""
        ds = MockDataSource()
        await ds.get_client()
        assert ds._initialized is True

        await ds.close()
        assert ds._initialized is False
        assert ds._client is None

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_close_allows_reinitialization(self) -> None:
        """测试 close 后可以重新初始化"""
        ds = MockDataSource()
        await ds.get_client()
        await ds.close()
        client2 = await ds.get_client()
        assert client2 == "mock_client"


class DataSourceWithFailedInit(DataSource[str]):
    """初始化失败的数据源"""

    def __init__(self) -> None:
        super().__init__()

    @property
    def name(self) -> str:
        return "failed_init"

    @property
    def required_config(self) -> list[str]:
        return []

    async def initialize(self) -> None:
        # 不设置 _client
        pass


class TestDataSourceFailedInit:
    """DataSource 初始化失败测试"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_client_raises_on_failed_init(self) -> None:
        """测试初始化失败时抛出异常"""
        ds = DataSourceWithFailedInit()
        with pytest.raises(RuntimeError) as exc_info:
            await ds.get_client()
        assert "初始化失败" in str(exc_info.value)
