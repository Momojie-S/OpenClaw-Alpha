# -*- coding: utf-8 -*-
"""技术指标 skill 测试配置"""

import pandas as pd
import pytest


@pytest.fixture
def sample_history_df():
    """模拟历史行情数据"""
    dates = pd.date_range(start="2026-01-01", periods=60, freq="D")
    df = pd.DataFrame(
        {
            "date": dates,
            "open": [10.0 + i * 0.1 for i in range(60)],
            "close": [10.2 + i * 0.1 for i in range(60)],
            "high": [10.5 + i * 0.1 for i in range(60)],
            "low": [9.8 + i * 0.1 for i in range(60)],
            "volume": [1000000 + i * 10000 for i in range(60)],
        }
    )
    return df


@pytest.fixture
def sample_trend_df():
    """模拟上涨趋势数据"""
    dates = pd.date_range(start="2026-01-01", periods=60, freq="D")
    df = pd.DataFrame(
        {
            "date": dates,
            "open": [10.0 + i * 0.2 for i in range(60)],
            "close": [10.3 + i * 0.2 for i in range(60)],
            "high": [10.6 + i * 0.2 for i in range(60)],
            "low": [9.9 + i * 0.2 for i in range(60)],
            "volume": [1000000 + i * 10000 for i in range(60)],
        }
    )
    return df


@pytest.fixture
def sample_downtrend_df():
    """模拟下跌趋势数据"""
    dates = pd.date_range(start="2026-01-01", periods=60, freq="D")
    df = pd.DataFrame(
        {
            "date": dates,
            "open": [20.0 - i * 0.2 for i in range(60)],
            "close": [19.7 - i * 0.2 for i in range(60)],
            "high": [20.3 - i * 0.2 for i in range(60)],
            "low": [19.5 - i * 0.2 for i in range(60)],
            "volume": [1000000 + i * 10000 for i in range(60)],
        }
    )
    return df
