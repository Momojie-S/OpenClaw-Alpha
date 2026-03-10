# -*- coding: utf-8 -*-
"""个股资金流向分析 Processor 测试"""

import pandas as pd
import pytest

from openclaw_alpha.skills.stock_fund_flow.stock_fund_flow_processor.stock_fund_flow_processor import (
    normalize_stock_code,
    calculate_summaries,
    analyze_trend,
    analyze_price_correlation,
    FundFlowSummary,
    FundFlowTrend,
    PriceCorrelation,
)


class TestNormalizeStockCode:
    """测试股票代码规范化"""

    def test_shanghai_stock(self):
        """测试上海股票"""
        code, market = normalize_stock_code("600519")
        assert code == "600519"
        assert market == "sh"

    def test_shenzhen_stock(self):
        """测试深圳股票"""
        code, market = normalize_stock_code("000001")
        assert code == "000001"
        assert market == "sz"

    def test_with_suffix(self):
        """测试带后缀的代码"""
        code, market = normalize_stock_code("000001.SZ")
        assert code == "000001"
        assert market == "sz"

        code, market = normalize_stock_code("600519.SH")
        assert code == "600519"
        assert market == "sh"


class TestCalculateSummaries:
    """测试资金流向汇总计算"""

    @pytest.fixture
    def sample_df(self):
        """创建测试数据"""
        data = {
            "date": ["2026-03-06", "2026-03-05", "2026-03-04"],
            "main_net_inflow": [1000000.0, -500000.0, 2000000.0],
            "main_net_ratio": [1.5, -0.8, 3.2],
            "super_large_net_inflow": [500000.0, -200000.0, 1000000.0],
            "large_net_inflow": [500000.0, -300000.0, 1000000.0],
            "medium_net_inflow": [-200000.0, 100000.0, -500000.0],
            "small_net_inflow": [-800000.0, 400000.0, -1500000.0],
        }
        df = pd.DataFrame(data)
        return df

    def test_calculate_today(self, sample_df):
        """测试今日汇总"""
        summaries = calculate_summaries(sample_df, [1])

        assert len(summaries) == 1
        assert summaries[0].period == "今日"
        assert summaries[0].main_net_inflow == 1000000.0
        assert summaries[0].main_net_ratio == 1.5

    def test_calculate_multi_periods(self, sample_df):
        """测试多周期汇总"""
        summaries = calculate_summaries(sample_df, [1, 3])

        assert len(summaries) == 2
        # 今日
        assert summaries[0].period == "今日"
        assert summaries[0].main_net_inflow == 1000000.0
        # 近3日（求和）
        assert summaries[1].period == "近3日"
        assert summaries[1].main_net_inflow == 2500000.0  # 100万 - 50万 + 200万

    def test_periods_exceed_data(self, sample_df):
        """测试周期超过数据量"""
        summaries = calculate_summaries(sample_df, [1, 3, 5, 10])

        # 只有 1 日和 3 日有数据
        assert len(summaries) == 2


class TestAnalyzeTrend:
    """测试资金趋势分析"""

    @pytest.fixture
    def continuous_inflow_df(self):
        """创建持续流入数据"""
        data = {
            "main_net_inflow": [1000000.0, 2000000.0, 1500000.0, 3000000.0, 2500000.0,
                               1800000.0, 2200000.0, 1600000.0, 1400000.0, 1900000.0],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def continuous_outflow_df(self):
        """创建持续流出数据"""
        data = {
            "main_net_inflow": [-1000000.0, -2000000.0, -1500000.0, -3000000.0, -2500000.0,
                               -1800000.0, -2200000.0, -1600000.0, -1400000.0, -1900000.0],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def oscillating_df(self):
        """创建震荡数据"""
        data = {
            "main_net_inflow": [1000000.0, -2000000.0, 1500000.0, -3000000.0, 2500000.0,
                               -1800000.0, 2200000.0, -1600000.0, 1400000.0, -1900000.0],
        }
        return pd.DataFrame(data)

    def test_continuous_inflow(self, continuous_inflow_df):
        """测试持续流入"""
        trend = analyze_trend(continuous_inflow_df, lookback=10)

        assert trend.trend == "持续流入"
        assert trend.consecutive_days == 10
        assert trend.avg_daily_inflow > 0

    def test_continuous_outflow(self, continuous_outflow_df):
        """测试持续流出"""
        trend = analyze_trend(continuous_outflow_df, lookback=10)

        assert trend.trend == "持续流出"
        assert trend.consecutive_days == -10
        assert trend.avg_daily_inflow < 0

    def test_oscillating(self, oscillating_df):
        """测试震荡"""
        trend = analyze_trend(oscillating_df, lookback=10)

        assert trend.trend == "震荡"
        assert trend.consecutive_days == 1  # 第一天是流入


class TestAnalyzePriceCorrelation:
    """测试价格关联分析"""

    @pytest.fixture
    def driven_df(self):
        """创建资金推动数据"""
        data = {
            "main_net_inflow": [1000000.0, 2000000.0, -500000.0, 3000000.0, -100000.0,
                               1500000.0, 2500000.0, -300000.0, 800000.0, 1200000.0],
            "pct_change": [1.0, 2.5, -0.5, 3.0, -0.1, 1.5, 2.0, -0.3, 0.8, 1.2],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def divergent_df(self):
        """创建资金背离数据"""
        data = {
            "main_net_inflow": [1000000.0, -2000000.0, 1500000.0, -3000000.0, 2500000.0,
                               -1800000.0, 2200000.0, -1600000.0, 1400000.0, -1900000.0],
            "pct_change": [-1.0, 2.0, -1.5, 3.0, -2.5, 1.8, -2.2, 1.6, -1.4, 1.9],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def neutral_df(self):
        """创建无明显关联数据"""
        data = {
            "main_net_inflow": [1000000.0, -2000000.0, 1500000.0, -3000000.0, 2500000.0],
            "pct_change": [1.0, -2.0, 1.5, 3.0, -2.5],  # 3 同向，2 背离
        }
        return pd.DataFrame(data)

    def test_driven(self, driven_df):
        """测试资金推动"""
        correlation = analyze_price_correlation(driven_df, lookback=10)

        assert correlation.correlation == "资金推动"

    def test_divergent(self, divergent_df):
        """测试资金背离"""
        correlation = analyze_price_correlation(divergent_df, lookback=10)

        assert correlation.correlation == "资金背离"

    def test_neutral(self, neutral_df):
        """测试无明显关联"""
        correlation = analyze_price_correlation(neutral_df, lookback=5)

        assert correlation.correlation == "无明显关联"
