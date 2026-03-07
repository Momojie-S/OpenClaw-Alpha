# -*- coding: utf-8 -*-
"""ETF Fetcher 测试"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import pandas as pd

from skills.etf_analysis.scripts.etf_fetcher.akshare_impl import (
    EtfFetcherAkshare,
    EtfSpot,
    EtfHistory,
)


class TestEtfFetcherAkshareTransform:
    """ETF Fetcher 转换逻辑测试"""

    @pytest.fixture
    def fetcher(self):
        """创建 Fetcher 实例"""
        return EtfFetcherAkshare()

    @pytest.fixture
    def sample_spot_df(self):
        """模拟实时行情数据"""
        return pd.DataFrame(
            {
                "代码": ["sz159915", "sz159919"],
                "名称": ["创业板ETF", "沪深300ETF"],
                "最新价": [2.0, 4.5],
                "涨跌幅": ["3.5%", "-1.2%"],
                "涨跌额": [0.07, -0.05],
                "成交额": [1000000000, 5000000000],  # 元
                "成交量": [5000000, 11000000],
                "今开": [1.95, 4.55],
                "最高": [2.05, 4.6],
                "最低": [1.94, 4.4],
                "昨收": [1.93, 4.55],
            }
        )

    @pytest.fixture
    def sample_history_df(self):
        """模拟历史数据"""
        return pd.DataFrame(
            {
                "date": ["2026-03-06", "2026-03-05"],
                "open": [2.0, 1.95],
                "high": [2.1, 2.0],
                "low": [1.95, 1.9],
                "close": [2.05, 1.98],
                "volume": [5000000, 4500000],
                "amount": [100000000, 90000000],
            }
        )

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_spot_transform(self, fetcher, sample_spot_df):
        """测试实时行情数据转换"""
        mock_ak = MagicMock()
        mock_ak.fund_etf_category_sina.return_value = sample_spot_df

        # Mock 数据源注册表
        mock_registry = MagicMock()
        mock_ds = MagicMock()
        mock_ds.get_client = AsyncMock(return_value=None)  # client 未使用
        mock_registry.get.return_value = mock_ds

        with patch(
            "skills.etf_analysis.scripts.etf_fetcher.akshare_impl.DataSourceRegistry.get_instance",
            return_value=mock_registry,
        ), patch.dict("sys.modules", {"akshare": mock_ak}):
            result = await fetcher._fetch_spot()

            assert len(result) == 2

            # 验证第一个 ETF
            etf1 = result[0]
            assert etf1.code == "sz159915"
            assert etf1.name == "创业板ETF"
            assert etf1.price == 2.0
            assert etf1.change_pct == 3.5
            assert etf1.change == 0.07
            assert etf1.amount == 10.0  # 10亿
            assert etf1.prev_close == 1.93

            # 验证第二个 ETF（负涨跌幅）
            etf2 = result[1]
            assert etf2.change_pct == -1.2
            assert etf2.amount == 50.0  # 50亿

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_history_transform(self, fetcher, sample_history_df):
        """测试历史数据转换"""
        mock_ak = MagicMock()
        mock_ak.fund_etf_hist_sina.return_value = sample_history_df

        # Mock 数据源注册表
        mock_registry = MagicMock()
        mock_ds = MagicMock()
        mock_ds.get_client = AsyncMock(return_value=None)
        mock_registry.get.return_value = mock_ds

        with patch(
            "skills.etf_analysis.scripts.etf_fetcher.akshare_impl.DataSourceRegistry.get_instance",
            return_value=mock_registry,
        ), patch.dict("sys.modules", {"akshare": mock_ak}):
            result = await fetcher._fetch_history("sz159915", days=2)

            assert len(result) == 2

            # 验证第一条数据
            hist1 = result[0]
            assert hist1.date == "2026-03-06"
            assert hist1.open == 2.0
            assert hist1.close == 2.05
            assert hist1.amount == 1.0  # 1亿

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_spot_empty(self, fetcher):
        """测试空数据返回"""
        mock_ak = MagicMock()
        mock_ak.fund_etf_category_sina.return_value = pd.DataFrame()

        # Mock 数据源注册表
        mock_registry = MagicMock()
        mock_ds = MagicMock()
        mock_ds.get_client = AsyncMock(return_value=None)
        mock_registry.get.return_value = mock_ds

        with patch(
            "skills.etf_analysis.scripts.etf_fetcher.akshare_impl.DataSourceRegistry.get_instance",
            return_value=mock_registry,
        ), patch.dict("sys.modules", {"akshare": mock_ak}):
            result = await fetcher._fetch_spot()
            assert result == []

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_history_empty(self, fetcher):
        """测试历史数据空返回"""
        mock_ak = MagicMock()
        # 返回空 DataFrame，但要有正确的列，否则会触发 retry
        mock_ak.fund_etf_hist_sina.return_value = pd.DataFrame(
            columns=["date", "open", "high", "low", "close", "volume", "amount"]
        )

        # Mock 数据源注册表
        mock_registry = MagicMock()
        mock_ds = MagicMock()
        mock_ds.get_client = AsyncMock(return_value=None)
        mock_registry.get.return_value = mock_ds

        with patch(
            "skills.etf_analysis.scripts.etf_fetcher.akshare_impl.DataSourceRegistry.get_instance",
            return_value=mock_registry,
        ), patch.dict("sys.modules", {"akshare": mock_ak}):
            result = await fetcher._fetch_history("sz159915", days=30)
            assert result == []


class TestEtfSpotDataClass:
    """EtfSpot 数据类测试"""

    def test_create_etf_spot(self):
        """创建 EtfSpot 实例"""
        etf = EtfSpot(
            code="sz159915",
            name="创业板ETF",
            price=2.0,
            change_pct=3.5,
            change=0.07,
            amount=10.0,
            volume=5000000,
            open=1.95,
            high=2.05,
            low=1.94,
            prev_close=1.93,
        )
        assert etf.code == "sz159915"
        assert etf.name == "创业板ETF"
        assert etf.price == 2.0


class TestEtfHistoryDataClass:
    """EtfHistory 数据类测试"""

    def test_create_etf_history(self):
        """创建 EtfHistory 实例"""
        hist = EtfHistory(
            date="2026-03-06",
            open=2.0,
            high=2.1,
            low=1.95,
            close=2.05,
            volume=5000000,
            amount=10.0,
        )
        assert hist.date == "2026-03-06"
        assert hist.open == 2.0
        assert hist.close == 2.05
