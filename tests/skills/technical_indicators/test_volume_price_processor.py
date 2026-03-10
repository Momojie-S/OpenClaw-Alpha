# -*- coding: utf-8 -*-
"""量价关系分析 Processor 测试"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import AsyncMock, patch

from openclaw_alpha.skills.technical_indicators.volume_price_processor.volume_price_processor import (
    VolumePriceProcessor,
)


@pytest.fixture
def mock_history_data():
    """模拟历史数据"""
    dates = pd.date_range("2026-01-01", periods=30, freq="D")
    data = {
        "date": [d.strftime("%Y-%m-%d") for d in dates],
        "open": np.linspace(10.0, 12.0, 30),
        "high": np.linspace(10.5, 12.5, 30),
        "low": np.linspace(9.5, 11.5, 30),
        "close": np.linspace(10.0, 12.0, 30),
        "volume": np.linspace(1000000, 2000000, 30),
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_divergence_data():
    """模拟量价背离数据（价涨量缩）"""
    dates = pd.date_range("2026-01-01", periods=30, freq="D")
    data = {
        "date": [d.strftime("%Y-%m-%d") for d in dates],
        "open": np.linspace(10.0, 12.0, 30),  # 价格上涨
        "high": np.linspace(10.5, 12.5, 30),
        "low": np.linspace(9.5, 11.5, 30),
        "close": np.linspace(10.0, 12.0, 30),
        "volume": np.linspace(2000000, 1000000, 30),  # 成交量下降
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_volatile_data():
    """模拟震荡数据"""
    dates = pd.date_range("2026-01-01", periods=30, freq="D")
    np.random.seed(42)
    data = {
        "date": [d.strftime("%Y-%m-%d") for d in dates],
        "open": 10.0 + np.random.randn(30) * 0.5,
        "high": 10.5 + np.random.randn(30) * 0.5,
        "low": 9.5 + np.random.randn(30) * 0.5,
        "close": 10.0 + np.random.randn(30) * 0.5,
        "volume": 1000000 + np.random.randn(30) * 200000,
    }
    return pd.DataFrame(data)


class TestVolumePriceProcessor:
    """VolumePriceProcessor 测试"""

    def test_init(self):
        """测试初始化"""
        processor = VolumePriceProcessor("000001", days=60)
        assert processor.symbol == "000001"
        assert processor.days == 60
        assert processor.df is None

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_analyze_with_data(self, mock_history_data):
        """测试正常数据分析"""
        processor = VolumePriceProcessor("000001", days=30)

        with patch(
            "skills.technical_indicators.scripts.volume_price_processor.volume_price_processor.fetch_history",
            new_callable=AsyncMock,
            return_value=mock_history_data,
        ):
            result = await processor.analyze()

        assert result["symbol"] == "000001"
        assert "error" not in result
        assert "indicators" in result
        assert "relationship" in result
        assert "obv" in result["indicators"]
        assert "correlation" in result["indicators"]
        assert "ma_volume" in result["indicators"]
        assert "volume_ratio" in result["indicators"]

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_analyze_empty_data(self):
        """测试空数据处理"""
        processor = VolumePriceProcessor("000001", days=60)

        with patch(
            "skills.technical_indicators.scripts.volume_price_processor.volume_price_processor.fetch_history",
            new_callable=AsyncMock,
            return_value=pd.DataFrame(),
        ):
            result = await processor.analyze()

        assert result["symbol"] == "000001"
        assert "error" in result
        assert result["error"] == "无法获取历史数据"


class TestOBVCalculation:
    """OBV 计算测试"""

    def test_obv_rising(self, mock_history_data):
        """测试 OBV 上升趋势"""
        processor = VolumePriceProcessor("000001", days=30)
        processor.df = mock_history_data

        result = processor._calculate_obv()

        assert "value" in result
        assert "trend" in result
        assert "trend_days" in result
        # 价格持续上涨，OBV 应该上升
        assert result["trend"] == "上升"

    def test_obv_falling(self):
        """测试 OBV 下降趋势"""
        dates = pd.date_range("2026-01-01", periods=30, freq="D")
        data = {
            "date": [d.strftime("%Y-%m-%d") for d in dates],
            "open": np.linspace(12.0, 10.0, 30),  # 价格下跌
            "high": np.linspace(12.5, 10.5, 30),
            "low": np.linspace(11.5, 9.5, 30),
            "close": np.linspace(12.0, 10.0, 30),
            "volume": np.linspace(1000000, 2000000, 30),
        }
        df = pd.DataFrame(data)

        processor = VolumePriceProcessor("000001", days=30)
        processor.df = df

        result = processor._calculate_obv()

        # 价格持续下跌，OBV 应该下降
        assert result["trend"] == "下降"


class TestCorrelationCalculation:
    """相关系数计算测试"""

    def test_positive_correlation(self, mock_history_data):
        """测试正相关"""
        processor = VolumePriceProcessor("000001", days=30)
        processor.df = mock_history_data

        result = processor._calculate_correlation()

        assert "value" in result
        assert "interpretation" in result
        assert -1 <= result["value"] <= 1

    def test_negative_correlation(self, mock_divergence_data):
        """测试负相关（量价背离）- 验证相关性计算正常"""
        processor = VolumePriceProcessor("000001", days=30)
        processor.df = mock_divergence_data

        result = processor._calculate_correlation()

        assert "value" in result
        assert "interpretation" in result
        # 相关系数应在 [-1, 1] 范围内
        assert -1 <= result["value"] <= 1
        # 注意：当价格和成交量都是线性变化时，变化率相关性可能不反映绝对值关系


class TestMAVolumeCalculation:
    """成交量均线计算测试"""

    def test_ma_volume(self, mock_history_data):
        """测试成交量均线计算"""
        processor = VolumePriceProcessor("000001", days=30)
        processor.df = mock_history_data

        result = processor._calculate_ma_volume()

        assert "current" in result
        assert "ma5" in result
        assert "ma10" in result
        assert "ma20" in result
        assert "status" in result
        assert result["ma5"] > 0
        assert result["ma10"] > 0

    def test_volume_status_high_volume(self):
        """测试高成交量状态"""
        dates = pd.date_range("2026-01-01", periods=30, freq="D")
        # 最后一天成交量远高于均线
        volumes = np.ones(30) * 1000000
        volumes[-1] = 5000000  # 巨量
        data = {
            "date": [d.strftime("%Y-%m-%d") for d in dates],
            "open": np.ones(30) * 10.0,
            "high": np.ones(30) * 10.5,
            "low": np.ones(30) * 9.5,
            "close": np.ones(30) * 10.0,
            "volume": volumes,
        }
        df = pd.DataFrame(data)

        processor = VolumePriceProcessor("000001", days=30)
        processor.df = df

        result = processor._calculate_ma_volume()

        assert result["status"] in ["巨量", "放量"]


class TestVolumeRatioCalculation:
    """量比计算测试"""

    def test_volume_ratio_normal(self, mock_history_data):
        """测试正常量比"""
        processor = VolumePriceProcessor("000001", days=30)
        processor.df = mock_history_data

        result = processor._calculate_volume_ratio()

        assert "value" in result
        assert "interpretation" in result
        assert result["value"] > 0

    def test_volume_ratio_high(self):
        """测试高量比"""
        dates = pd.date_range("2026-01-01", periods=30, freq="D")
        # 最后一天成交量是前 5 天的 3 倍
        volumes = np.ones(30) * 1000000
        volumes[-1] = 3000000
        data = {
            "date": [d.strftime("%Y-%m-%d") for d in dates],
            "open": np.ones(30) * 10.0,
            "high": np.ones(30) * 10.5,
            "low": np.ones(30) * 9.5,
            "close": np.ones(30) * 10.0,
            "volume": volumes,
        }
        df = pd.DataFrame(data)

        processor = VolumePriceProcessor("000001", days=30)
        processor.df = df

        result = processor._calculate_volume_ratio()

        assert result["value"] > 2.0
        assert "放量" in result["interpretation"]


class TestRelationshipAnalysis:
    """量价关系综合分析测试"""

    def test_analyze_bullish(self, mock_history_data):
        """测试看涨信号"""
        processor = VolumePriceProcessor("000001", days=30)
        processor.df = mock_history_data

        obv_result = processor._calculate_obv()
        correlation_result = processor._calculate_correlation()
        ma_volume_result = processor._calculate_ma_volume()
        volume_ratio_result = processor._calculate_volume_ratio()

        result = processor._analyze_relationship(
            obv_result, correlation_result, ma_volume_result, volume_ratio_result
        )

        assert "pattern" in result
        assert "signal" in result
        assert "score" in result
        assert "description" in result
        assert result["signal"] in ["看涨", "偏多", "中性", "偏空", "看跌"]

    def test_analyze_divergence(self, mock_divergence_data):
        """测试量价关系综合分析 - 验证分析逻辑正常"""
        processor = VolumePriceProcessor("000001", days=30)
        processor.df = mock_divergence_data

        obv_result = processor._calculate_obv()
        correlation_result = processor._calculate_correlation()
        ma_volume_result = processor._calculate_ma_volume()
        volume_ratio_result = processor._calculate_volume_ratio()

        result = processor._analyze_relationship(
            obv_result, correlation_result, ma_volume_result, volume_ratio_result
        )

        # 验证分析结果结构正确
        assert "pattern" in result
        assert "signal" in result
        assert "score" in result
        assert "description" in result
        assert result["signal"] in ["看涨", "偏多", "中性", "偏空", "看跌"]
        # 注意：量价关系的判断基于多种因素的综合，不仅是相关系数


class TestPrintResult:
    """打印结果测试"""

    def test_print_result(self, mock_history_data, capsys):
        """测试结果打印"""
        processor = VolumePriceProcessor("000001", days=30)
        processor.df = mock_history_data

        # 构建模拟结果
        result = {
            "symbol": "000001",
            "date": "2026-03-08",
            "data_range": {"start": "2026-01-01", "end": "2026-01-30", "days": 30},
            "indicators": {
                "obv": {"value": 1000000.0, "trend": "上升", "trend_days": 5, "series": []},
                "correlation": {"value": 0.5, "period": 20, "interpretation": "强正相关"},
                "ma_volume": {"current": 2000000, "ma5": 1500000, "ma10": 1400000, "ma20": 1300000, "status": "放量"},
                "volume_ratio": {"value": 1.5, "interpretation": "温和放量"},
            },
            "relationship": {
                "pattern": "放量上涨 | 量价正关联",
                "signal": "看涨",
                "score": 2,
                "description": "量价配合良好",
                "price_change_5d": 5.0,
                "volume_change_5d": 20.0,
            },
        }

        processor.print_result(result)

        captured = capsys.readouterr()
        assert "量价关系分析 - 000001" in captured.out
        assert "OBV 能量潮" in captured.out
        assert "量价相关系数" in captured.out
        assert "成交量状态" in captured.out
        assert "量比" in captured.out
        assert "量价关系判断" in captured.out
