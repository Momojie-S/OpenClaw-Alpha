# -*- coding: utf-8 -*-
"""Fetcher 测试"""

import pytest

from openclaw_alpha.core.exceptions import (
    DataSourceUnavailableError,
    InsufficientCreditError,
    MissingConfigError,
    NoAvailableMethodError,
)
from openclaw_alpha.core.fetcher import FetchMethod, Fetcher
from openclaw_alpha.core.registry import DataSourceRegistry


class MockFetchMethod(FetchMethod):
    """Mock FetchMethod 用于测试"""

    name = "mock_method"
    required_data_source = "mock_ds"
    priority = 0

    def __init__(self, return_value: str = "mock_data"):
        self.return_value = return_value
        self.fetch_called = False

    async def fetch(self, *args, **kwargs):
        self.fetch_called = True
        return self.return_value


class HighPriorityMethod(FetchMethod):
    """高优先级方法"""

    name = "high_priority_method"
    required_data_source = "high_ds"
    priority = 100

    async def fetch(self, *args, **kwargs):
        return "high_priority_data"


class LowPriorityMethod(FetchMethod):
    """低优先级方法"""

    name = "low_priority_method"
    required_data_source = "low_ds"
    priority = 10

    async def fetch(self, *args, **kwargs):
        return "low_priority_data"


class MockFetcher(Fetcher):
    """Mock Fetcher 用于测试"""

    name = "mock_fetcher"


class TestFetchMethod:
    """FetchMethod 测试类"""

    def test_is_available_registered(self, monkeypatch):
        """测试数据源已注册且配置满足"""
        from openclaw_alpha.core.data_source import DataSource

        class TestDataSource(DataSource):
            @property
            def name(self) -> str:
                return "test_ds_for_method"

            @property
            def required_config(self) -> list[str]:
                return ["TEST_METHOD_TOKEN"]

            async def initialize(self) -> None:
                self._client = "test_client"

        registry = DataSourceRegistry.get_instance()
        registry.register(TestDataSource)

        class TestMethod(FetchMethod):
            name = "test_method"
            required_data_source = "test_ds_for_method"
            priority = 0

            async def fetch(self, *args, **kwargs):
                return "test_data"

        method = TestMethod()

        # 未设置环境变量
        monkeypatch.delenv("TEST_METHOD_TOKEN", raising=False)
        available, error = method.is_available()
        assert available is False
        assert isinstance(error, MissingConfigError)

        # 设置环境变量
        monkeypatch.setenv("TEST_METHOD_TOKEN", "test_value")
        available, error = method.is_available()
        assert available is True
        assert error is None

    def test_is_available_not_registered(self):
        """测试数据源未注册"""

        class TestMethod(FetchMethod):
            name = "test_method_not_registered"
            required_data_source = "not_registered_ds"
            priority = 0

            async def fetch(self, *args, **kwargs):
                return "test_data"

        method = TestMethod()
        available, error = method.is_available()
        assert available is False
        assert isinstance(error, DataSourceUnavailableError)
        assert "未注册" in str(error)

    def test_is_available_credit_check(self, monkeypatch):
        """测试积分校验"""
        from openclaw_alpha.core.data_source import DataSource

        class CreditDS(DataSource):
            @property
            def name(self) -> str:
                return "credit_ds"

            @property
            def required_config(self) -> list[str]:
                return []

            @property
            def credit(self) -> int:
                return 100  # 用户积分 100

        registry = DataSourceRegistry.get_instance()
        registry.register(CreditDS)

        class LowCreditMethod(FetchMethod):
            name = "low_credit_method"
            required_data_source = "credit_ds"
            required_credit = 50  # 需要 50 积分

            async def fetch(self, *args, **kwargs):
                return "data"

        class HighCreditMethod(FetchMethod):
            name = "high_credit_method"
            required_data_source = "credit_ds"
            required_credit = 200  # 需要 200 积分

            async def fetch(self, *args, **kwargs):
                return "data"

        # 积分足够
        low_method = LowCreditMethod()
        available, error = low_method.is_available()
        assert available is True
        assert error is None

        # 积分不足
        high_method = HighCreditMethod()
        available, error = high_method.is_available()
        assert available is False
        assert isinstance(error, InsufficientCreditError)
        assert error.required == 200
        assert error.actual == 100


class TestFetcher:
    """Fetcher 测试类"""

    def test_register(self):
        """测试注册 FetchMethod"""
        fetcher = MockFetcher()
        method = MockFetchMethod()

        fetcher.register(method)

        assert len(fetcher._methods) == 1
        assert fetcher._methods[0] is method

    def test_register_with_priority_override(self):
        """测试注册时覆盖优先级"""
        fetcher = MockFetcher()
        method = MockFetchMethod()
        method.priority = 0

        fetcher.register(method, priority=100)

        assert method.priority == 100

    def test_select_available_by_priority(self, monkeypatch):
        """测试按优先级选择可用实现"""
        from openclaw_alpha.core.data_source import DataSource

        # 注册两个数据源
        class HighDS(DataSource):
            @property
            def name(self) -> str:
                return "high_ds"

            @property
            def required_config(self) -> list[str]:
                return []

        class LowDS(DataSource):
            @property
            def name(self) -> str:
                return "low_ds"

            @property
            def required_config(self) -> list[str]:
                return []

        registry = DataSourceRegistry.get_instance()
        registry.register(HighDS)
        registry.register(LowDS)

        fetcher = MockFetcher()
        fetcher.register(HighPriorityMethod())
        fetcher.register(LowPriorityMethod())

        method, errors = fetcher._select_available()

        assert method is not None
        assert method.name == "high_priority_method"
        assert method.priority == 100

    def test_select_available_skip_unavailable(self, monkeypatch):
        """测试跳过不可用的实现，选择次优"""
        from openclaw_alpha.core.data_source import DataSource

        class HighDS(DataSource):
            @property
            def name(self) -> str:
                return "high_ds_unavailable"

            @property
            def required_config(self) -> list[str]:
                return ["HIGH_TOKEN"]

        class LowDS(DataSource):
            @property
            def name(self) -> str:
                return "low_ds_available"

            @property
            def required_config(self) -> list[str]:
                return []

        registry = DataSourceRegistry.get_instance()
        registry.register(HighDS)
        registry.register(LowDS)

        class HighMethod(FetchMethod):
            name = "high_method_unavailable"
            required_data_source = "high_ds_unavailable"
            priority = 100

            async def fetch(self, *args, **kwargs):
                return "high"

        class LowMethod(FetchMethod):
            name = "low_method_available"
            required_data_source = "low_ds_available"
            priority = 10

            async def fetch(self, *args, **kwargs):
                return "low"

        fetcher = MockFetcher()
        fetcher.register(HighMethod())
        fetcher.register(LowMethod())

        # 高优先级数据源不可用
        monkeypatch.delenv("HIGH_TOKEN", raising=False)

        method, errors = fetcher._select_available()

        # 应该选择低优先级但可用的实现
        assert method is not None
        assert method.name == "low_method_available"
        # 错误列表应包含高优先级的失败原因
        assert len(errors) == 1
        assert isinstance(errors[0], MissingConfigError)

    def test_select_available_no_available(self):
        """测试所有实现都不可用时返回 None 和错误列表"""
        fetcher = MockFetcher()

        class UnavailableMethod(FetchMethod):
            name = "unavailable_method"
            required_data_source = "not_exist_ds"
            priority = 10

            async def fetch(self, *args, **kwargs):
                return "data"

        fetcher.register(UnavailableMethod())

        method, errors = fetcher._select_available()

        assert method is None
        assert len(errors) == 1
        assert isinstance(errors[0], DataSourceUnavailableError)
        assert "未注册" in str(errors[0])

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_fetch(self, monkeypatch):
        """测试 fetch 方法调用选中的实现"""
        from openclaw_alpha.core.data_source import DataSource

        class TestDS(DataSource):
            @property
            def name(self) -> str:
                return "fetch_test_ds"

            @property
            def required_config(self) -> list[str]:
                return []

        registry = DataSourceRegistry.get_instance()
        registry.register(TestDS)

        class TestMethod(FetchMethod):
            name = "fetch_test_method"
            required_data_source = "fetch_test_ds"
            priority = 10

            async def fetch(self, *args, **kwargs):
                return {"data": "test_result", "args": args, "kwargs": kwargs}

        fetcher = MockFetcher()
        fetcher.register(TestMethod())

        result = await fetcher.fetch("arg1", key="value")

        assert result["data"] == "test_result"
        assert result["args"] == ("arg1",)
        assert result["kwargs"] == {"key": "value"}

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_fetch_no_available_raises(self):
        """测试 fetch 时无可用实现抛出异常"""
        fetcher = MockFetcher()

        class UnavailableMethod(FetchMethod):
            name = "unavailable_fetch_method"
            required_data_source = "not_exist_ds"
            priority = 10

            async def fetch(self, *args, **kwargs):
                return "data"

        fetcher.register(UnavailableMethod())

        with pytest.raises(NoAvailableMethodError) as exc_info:
            await fetcher.fetch()

        # 检查异常信息包含失败原因
        assert "mock_fetcher" in str(exc_info.value)
        assert "未注册" in str(exc_info.value) or "不可用" in str(exc_info.value)
