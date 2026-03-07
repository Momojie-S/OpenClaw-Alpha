# -*- coding: utf-8 -*-
"""DataSource 测试"""

import asyncio

import pytest

from openclaw_alpha.core.data_source import DataSource


class MockDataSource(DataSource):
    """Mock 数据源用于测试"""

    @property
    def name(self) -> str:
        return "mock_ds"

    @property
    def required_config(self) -> list[str]:
        return ["MOCK_TOKEN"]

    async def initialize(self) -> None:
        """模拟初始化"""
        await asyncio.sleep(0.01)  # 模拟异步初始化
        self._client = "mock_client"


class NoConfigMockDataSource(DataSource):
    """无需配置的数据源"""

    @property
    def name(self) -> str:
        return "no_config_ds"

    @property
    def required_config(self) -> list[str]:
        return []

    async def initialize(self) -> None:
        self._client = "no_config_client"


class TestDataSourceClass:
    """DataSource 测试类"""

    def test_is_available_with_config(self, monkeypatch):
        """测试需要配置的数据源可用性检查"""
        ds = MockDataSource()

        # 未设置环境变量
        monkeypatch.delenv("MOCK_TOKEN", raising=False)
        assert ds.is_available() is False

        # 设置环境变量
        monkeypatch.setenv("MOCK_TOKEN", "test_token")
        assert ds.is_available() is True

    def test_is_available_no_config(self):
        """测试无需配置的数据源可用性检查"""
        ds = NoConfigMockDataSource()
        assert ds.is_available() is True

    def test_is_available_empty_value(self, monkeypatch):
        """测试环境变量为空字符串时不可用"""
        ds = MockDataSource()

        monkeypatch.setenv("MOCK_TOKEN", "")
        assert ds.is_available() is False

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_client_lazy_loading(self):
        """测试懒加载：首次获取时初始化"""
        ds = MockDataSource()
        assert ds._initialized is False
        assert ds._client is None

        client = await ds.get_client()
        assert ds._initialized is True
        assert client == "mock_client"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_client_cached(self):
        """测试客户端缓存：多次获取返回同一实例"""
        ds = MockDataSource()

        client1 = await ds.get_client()
        client2 = await ds.get_client()

        assert client1 is client2

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_client_concurrent(self):
        """测试并发获取客户端：只初始化一次"""
        ds = MockDataSource()

        # 并发调用 10 次
        tasks = [ds.get_client() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # 所有结果应该是同一个实例
        assert all(r is results[0] for r in results)

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_close(self):
        """测试资源清理"""
        ds = MockDataSource()
        await ds.get_client()
        assert ds._initialized is True

        await ds.close()
        assert ds._initialized is False
        assert ds._client is None

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_client_after_close(self):
        """测试关闭后重新获取：可以再次初始化"""
        ds = MockDataSource()

        client1 = await ds.get_client()
        await ds.close()
        client2 = await ds.get_client()

        assert client1 == client2 == "mock_client"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_initialize_failure(self):
        """测试初始化失败抛出异常"""

        class FailureMockDataSource(DataSource):
            @property
            def name(self) -> str:
                return "fail_ds"

            @property
            def required_config(self) -> list[str]:
                return []

            async def initialize(self) -> None:
                # 初始化但不设置 _client
                pass

        ds = FailureMockDataSource()

        with pytest.raises(RuntimeError) as exc_info:
            await ds.get_client()

        assert "初始化失败" in str(exc_info.value)
