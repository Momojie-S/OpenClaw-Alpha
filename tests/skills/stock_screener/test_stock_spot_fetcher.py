# -*- coding: utf-8 -*-
"""StockSpotFetcher 测试"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock

import pandas as pd

from openclaw_alpha.skills.stock_screener.stock_spot_fetcher.stock_spot_fetcher import (
    StockSpot,
    StockSpotFetcher,
)


# Fixture 数据
FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_fixture() -> pd.DataFrame:
    """加载 fixture 数据"""
    with open(FIXTURE_DIR / "spot_response.json", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


class TestStockSpotFetcherAkshare:
    """测试 AKShare 实现"""

    @pytest.fixture
    def fetcher(self):
        """创建 Fetcher 实例"""
        from openclaw_alpha.skills.stock_screener.stock_spot_fetcher.akshare import (
            StockSpotFetcherAkshare,
        )

        return StockSpotFetcherAkshare()

    def test_transform_basic(self, fetcher):
        """测试基本转换"""
        df = load_fixture()
        result = fetcher._transform(df)

        assert len(result) == 10
        assert all(isinstance(s, StockSpot) for s in result)

    def test_transform_field_mapping(self, fetcher):
        """测试字段映射"""
        df = load_fixture()
        result = fetcher._transform(df)

        # 检查第一只股票（平安银行）
        spot = result[0]
        assert spot.code == "000001"
        assert spot.name == "平安银行"
        assert spot.change_pct == 2.35
        assert spot.turnover_rate == 1.25
        assert spot.price == 12.5

    def test_transform_unit_conversion(self, fetcher):
        """测试单位转换"""
        df = load_fixture()
        result = fetcher._transform(df)

        # 成交额：元 -> 亿元
        assert result[0].amount == 15.0  # 15亿
        # 市值：元 -> 亿元
        assert result[0].market_cap == 2500.0  # 2500亿

    def test_transform_skip_nan(self, fetcher):
        """测试跳过无效数据"""
        # 添加一条无效数据
        df = load_fixture()
        invalid_row = {
            "代码": "999999",
            "名称": "无效股票",
            "涨跌幅": None,
            "换手率": 1.0,
            "成交额": 100000000,
            "最新价": None,
            "总市值": 1000000000,
        }
        df = pd.concat([df, pd.DataFrame([invalid_row])], ignore_index=True)

        result = fetcher._transform(df)
        # 应该只有 10 条有效数据
        assert len(result) == 10

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_fetch_with_mock(self, fetcher):
        """测试完整获取流程（Mock API）"""
        df = load_fixture()

        with patch.object(
            fetcher, "_call_api", new_callable=AsyncMock, return_value=df
        ):
            result = await fetcher.fetch()

            assert len(result) == 10
            assert all(isinstance(s, StockSpot) for s in result)
