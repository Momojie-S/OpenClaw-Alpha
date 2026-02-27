# -*- coding: utf-8 -*-
"""异常类测试"""

import pytest

from openclaw_alpha.core.exceptions import (
    DuplicateDataSourceError,
    NoAvailableImplementationError,
)


class TestDuplicateDataSourceError:
    """DuplicateDataSourceError 测试"""

    def test_init_with_name(self) -> None:
        """测试使用名称初始化"""
        error = DuplicateDataSourceError("tushare")
        assert error.name == "tushare"
        assert "tushare" in str(error)

    def test_raise_and_catch(self) -> None:
        """测试抛出和捕获"""
        with pytest.raises(DuplicateDataSourceError) as exc_info:
            raise DuplicateDataSourceError("akshare")
        assert exc_info.value.name == "akshare"


class TestNoAvailableImplementationError:
    """NoAvailableImplementationError 测试"""

    def test_init_with_empty_implementations(self) -> None:
        """测试使用空实现列表初始化"""
        error = NoAvailableImplementationError("MyStrategy", [])
        assert error.strategy_name == "MyStrategy"
        assert error.checked_implementations == []

    def test_init_with_implementations(self) -> None:
        """测试使用实现列表初始化"""
        impls = ["TushareImpl", "AkshareImpl"]
        error = NoAvailableImplementationError("StockQuoteStrategy", impls)
        assert error.strategy_name == "StockQuoteStrategy"
        assert error.checked_implementations == impls
        assert "StockQuoteStrategy" in str(error)
        assert "TushareImpl" in str(error)

    def test_raise_and_catch(self) -> None:
        """测试抛出和捕获"""
        with pytest.raises(NoAvailableImplementationError) as exc_info:
            raise NoAvailableImplementationError("TestStrategy", ["Impl1"])
        assert exc_info.value.strategy_name == "TestStrategy"
        assert exc_info.value.checked_implementations == ["Impl1"]
