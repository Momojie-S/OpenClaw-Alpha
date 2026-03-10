# -*- coding: utf-8 -*-
"""回测数据适配器测试"""

import pytest
import pandas as pd
from datetime import datetime

from openclaw_alpha.skills.backtest.backtest_processor.data_adapter import DataAdapter


class TestDataAdapter:
    """测试 DataAdapter 类"""

    def test_transform_valid_data(self):
        """测试有效数据转换"""
        adapter = DataAdapter()

        # 创建测试数据（使用英文列名，与 history_fetcher 输出一致）
        df = pd.DataFrame({
            "date": ["2026-03-01", "2026-03-02", "2026-03-03"],
            "open": [10.0, 10.5, 11.0],
            "close": [10.2, 10.8, 11.2],
            "high": [10.5, 11.0, 11.5],
            "low": [9.8, 10.3, 10.8],
            "volume": [1000000, 1200000, 1100000],
        })

        result = adapter.transform_to_backtrader(df, "600000")

        assert result is not None
        # 使用 params.name 而不是 .name
        assert result.params.name == "600000"

    def test_transform_empty_data(self):
        """测试空数据"""
        adapter = DataAdapter()
        df = pd.DataFrame()

        with pytest.raises(ValueError, match="数据为空"):
            adapter.transform_to_backtrader(df, "600000")

    def test_transform_missing_column(self):
        """测试缺少必需列"""
        adapter = DataAdapter()
        df = pd.DataFrame({
            "date": ["2026-03-01"],
            "open": [10.0],
            # 缺少 close, high, low, volume
        })

        with pytest.raises(ValueError, match="缺少必需列"):
            adapter.transform_to_backtrader(df, "600000")

    def test_transform_datetime_index(self):
        """测试日期索引转换"""
        adapter = DataAdapter()

        # 创建测试数据（使用英文列名，与 history_fetcher 输出一致）
        df = pd.DataFrame({
            "date": ["2026-03-01", "2026-03-02"],
            "open": [10.0, 10.5],
            "close": [10.2, 10.8],
            "high": [10.5, 11.0],
            "low": [9.8, 10.3],
            "volume": [1000000, 1200000],
        })

        result = adapter.transform_to_backtrader(df, "600000")

        # 验证数据源已正确设置
        assert result.params.name == "600000"


class TestDataAdapterFetch:
    """测试数据获取（需要网络）"""

    @pytest.mark.skip(reason="需要网络，不稳定")
    def test_fetch_invalid_stock(self):
        """测试无效股票代码"""
        pass

    @pytest.mark.skip(reason="需要网络，不稳定")
    def test_fetch_empty_period(self):
        """测试无数据期间"""
        pass
