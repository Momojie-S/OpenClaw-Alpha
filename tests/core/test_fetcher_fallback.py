# -*- coding: utf-8 -*-
"""Fetcher 降级逻辑测试"""

import pytest

from openclaw_alpha.core.exceptions import (
    DataSourceUnavailableError,
    MissingConfigError,
    NoAvailableMethodError,
)
from openclaw_alpha.core.fetcher import Fetcher, FetchMethod


class MockFetchMethod(FetchMethod):
    """Mock FetchMethod 用于测试"""

    def __init__(
        self,
        name: str,
        data_source: str,
        priority: int = 0,
        available: bool = True,
        available_error: DataSourceUnavailableError | None = None,
        raise_error: Exception | None = None,
        return_value: str = "success",
    ):
        self.name = name
        self.required_data_source = data_source
        self.required_credit = 0
        self.priority = priority
        self._available = available
        self._available_error = available_error
        self._raise_error = raise_error
        self._return_value = return_value

    def is_available(self) -> tuple[bool, DataSourceUnavailableError | None]:
        return (self._available, self._available_error)

    async def fetch(self, *args, **kwargs) -> str:
        if self._raise_error:
            raise self._raise_error
        return self._return_value


class TestFetcherFallback:
    """Fetcher 降级逻辑测试"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_check_fail_fallback(self):
        """测试：检查失败降级到下一个 Method"""
        # 创建 Fetcher
        fetcher = Fetcher()
        fetcher.name = "test_fetcher"

        # 高优先级 Method 检查失败
        method1 = MockFetchMethod(
            name="method1",
            data_source="ds1",
            priority=10,
            available=False,
            available_error=MissingConfigError("ds1", ["TOKEN"]),
        )
        # 低优先级 Method 可用
        method2 = MockFetchMethod(
            name="method2",
            data_source="ds2",
            priority=5,
            available=True,
            return_value="fallback_success",
        )

        fetcher.register(method1)
        fetcher.register(method2)

        # 执行：应该降级到 method2
        result = await fetcher.fetch()
        assert result == "fallback_success"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_exec_fail_fallback(self):
        """测试：执行失败（任何异常）降级到下一个 Method"""
        fetcher = Fetcher()
        fetcher.name = "test_fetcher"

        # 高优先级 Method 执行失败
        method1 = MockFetchMethod(
            name="method1",
            data_source="ds1",
            priority=10,
            available=True,
            raise_error=TimeoutError("API timeout"),
        )
        # 低优先级 Method 成功
        method2 = MockFetchMethod(
            name="method2",
            data_source="ds2",
            priority=5,
            available=True,
            return_value="fallback_success",
        )

        fetcher.register(method1)
        fetcher.register(method2)

        # 执行：应该降级到 method2
        result = await fetcher.fetch()
        assert result == "fallback_success"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_all_fail_with_distinct_errors(self):
        """测试：所有 Method 失败，返回完整错误信息（区分检查错误和执行错误）"""
        fetcher = Fetcher()
        fetcher.name = "test_fetcher"

        # Method 1: 检查失败（配置缺失）
        method1 = MockFetchMethod(
            name="method1",
            data_source="ds1",
            priority=10,
            available=False,
            available_error=MissingConfigError("ds1", ["TOKEN"]),
        )
        # Method 2: 执行失败（网络错误）
        method2 = MockFetchMethod(
            name="method2",
            data_source="ds2",
            priority=5,
            available=True,
            raise_error=ConnectionError("Network unreachable"),
        )

        fetcher.register(method1)
        fetcher.register(method2)

        # 执行：应该抛出 NoAvailableMethodError
        with pytest.raises(NoAvailableMethodError) as exc_info:
            await fetcher.fetch()

        error = exc_info.value
        # 验证错误信息区分了检查错误和执行错误
        error_msg = str(error)
        assert "检查失败" in error_msg
        assert "执行失败" in error_msg
        assert "缺少配置" in error_msg
        assert "ConnectionError" in error_msg

        # 验证错误列表
        assert len(error.check_errors) == 1
        assert len(error.exec_errors) == 1
        assert isinstance(error.check_errors[0], MissingConfigError)
        assert isinstance(error.exec_errors[0], ConnectionError)

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_priority_order(self):
        """测试：按优先级降序尝试"""
        fetcher = Fetcher()
        fetcher.name = "test_fetcher"

        # 低优先级先注册
        method1 = MockFetchMethod(
            name="low_priority",
            data_source="ds1",
            priority=5,
            available=True,
            return_value="low",
        )
        # 高优先级后注册
        method2 = MockFetchMethod(
            name="high_priority",
            data_source="ds2",
            priority=10,
            available=True,
            return_value="high",
        )

        fetcher.register(method1)
        fetcher.register(method2)

        # 执行：应该使用高优先级的 method2
        result = await fetcher.fetch()
        assert result == "high"
