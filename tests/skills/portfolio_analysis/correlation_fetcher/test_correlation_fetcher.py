# -*- coding: utf-8 -*-
"""持仓相关性 Fetcher 测试"""

import pandas as pd
import pytest
from unittest.mock import AsyncMock, patch

from openclaw_alpha.core.registry import DataSourceRegistry
from openclaw_alpha.data_sources import AkshareDataSource


@pytest.fixture(autouse=True)
def reset_registry():
    """每个测试前重置注册表"""
    registry = DataSourceRegistry.get_instance()
    registry.reset()
    registry.register(AkshareDataSource)
    yield
    registry.reset()


@pytest.fixture
def mock_akshare_data():
    """模拟 AKShare 返回数据"""
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    return pd.DataFrame(
        {
            "日期": dates,
            "收盘": 100 + pd.Series(range(30)),
        }
    )


class TestCorrelationFetcherAkshare:
    """测试 AKShare 实现"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_single_stock(self, mock_akshare_data):
        """测试获取单只股票数据"""
        from openclaw_alpha.skills.portfolio_analysis.correlation_fetcher.correlation_fetcher import (
            CorrelationFetcherAkshare,
        )

        method = CorrelationFetcherAkshare()

        # Mock AKShare API
        with patch(
            "skills.portfolio_analysis.scripts.correlation_fetcher.correlation_fetcher.ak.stock_zh_a_hist",
            return_value=mock_akshare_data,
        ):
            data = await method.fetch(["000001"], days=30)

        assert "000001" in data
        assert isinstance(data["000001"], pd.DataFrame)
        assert "date" in data["000001"].columns
        assert "close" in data["000001"].columns

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_multiple_stocks(self, mock_akshare_data):
        """测试获取多只股票数据"""
        from openclaw_alpha.skills.portfolio_analysis.correlation_fetcher.correlation_fetcher import (
            CorrelationFetcherAkshare,
        )

        method = CorrelationFetcherAkshare()

        # Mock AKShare API
        with patch(
            "skills.portfolio_analysis.scripts.correlation_fetcher.correlation_fetcher.ak.stock_zh_a_hist",
            return_value=mock_akshare_data,
        ):
            data = await method.fetch(["000001", "600000"], days=30)

        assert len(data) == 2
        assert "000001" in data
        assert "600000" in data

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_fetch_empty_codes_raises_error(self):
        """测试空代码列表抛出异常"""
        from openclaw_alpha.skills.portfolio_analysis.correlation_fetcher.correlation_fetcher import (
            CorrelationFetcherAkshare,
        )

        method = CorrelationFetcherAkshare()

        with pytest.raises(ValueError, match="股票代码列表不能为空"):
            await method.fetch([])

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_invalid_code_logs_warning(self, mock_akshare_data):
        """测试无效代码记录警告"""
        from openclaw_alpha.skills.portfolio_analysis.correlation_fetcher.correlation_fetcher import (
            CorrelationFetcherAkshare,
        )

        method = CorrelationFetcherAkshare()

        # Mock AKShare API - 返回空数据
        with patch(
            "skills.portfolio_analysis.scripts.correlation_fetcher.correlation_fetcher.ak.stock_zh_a_hist",
            return_value=pd.DataFrame(),
        ):
            with pytest.raises(RuntimeError, match="所有股票数据获取失败"):
                await method.fetch(["999999"], days=10)


class TestCorrelationFetcher:
    """测试 Fetcher 入口"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_function(self, mock_akshare_data):
        """测试便捷函数"""
        from openclaw_alpha.skills.portfolio_analysis.correlation_fetcher.correlation_fetcher import (
            fetch,
        )

        with patch(
            "skills.portfolio_analysis.scripts.correlation_fetcher.correlation_fetcher.ak.stock_zh_a_hist",
            return_value=mock_akshare_data,
        ):
            data = await fetch(["000001"], days=30)

        assert "000001" in data
        assert isinstance(data["000001"], pd.DataFrame)

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetcher_entry(self, mock_akshare_data):
        """测试 Fetcher 入口类"""
        from openclaw_alpha.skills.portfolio_analysis.correlation_fetcher.correlation_fetcher import (
            CorrelationFetcher,
        )

        fetcher = CorrelationFetcher()

        with patch(
            "skills.portfolio_analysis.scripts.correlation_fetcher.correlation_fetcher.ak.stock_zh_a_hist",
            return_value=mock_akshare_data,
        ):
            data = await fetcher.fetch(["000001"], days=30)

        assert "000001" in data
