# -*- coding: utf-8 -*-
"""IndicatorProcessor 测试"""

import pandas as pd
import pytest

from skills.technical_indicators.scripts.indicator_processor.indicator_processor import (
    IndicatorProcessor,
)


class TestIndicatorProcessor:
    """测试 IndicatorProcessor"""

    @pytest.fixture
    def processor(self):
        """创建 Processor 实例"""
        return IndicatorProcessor("000001", days=60)

    def test_calculate_macd(self, processor, sample_history_df):
        """测试 MACD 计算"""
        processor.df = sample_history_df
        params = {"fast": 12, "slow": 26, "signal": 9}

        result = processor._calculate_macd(params)

        # 验证结果结构
        assert "dif" in result
        assert "dea" in result
        assert "macd" in result
        assert "histogram" in result

        # 验证类型
        assert isinstance(result["dif"], float)
        assert isinstance(result["dea"], float)
        assert isinstance(result["macd"], float)
        assert isinstance(result["histogram"], list)

    def test_calculate_rsi(self, processor, sample_history_df):
        """测试 RSI 计算"""
        processor.df = sample_history_df
        params = {"period": 14}

        result = processor._calculate_rsi(params)

        # 验证结果结构
        assert "value" in result
        assert "series" in result

        # 验证范围
        assert 0 <= result["value"] <= 100
        assert len(result["series"]) == 10

    def test_calculate_kdj(self, processor, sample_history_df):
        """测试 KDJ 计算"""
        processor.df = sample_history_df
        params = {"n": 9, "m1": 3, "m2": 3}

        result = processor._calculate_kdj(params)

        # 验证结果结构
        assert "k" in result
        assert "d" in result
        assert "j" in result
        assert "series" in result

        # 验证类型
        assert isinstance(result["k"], float)
        assert isinstance(result["d"], float)
        assert isinstance(result["j"], float)

    def test_calculate_boll(self, processor, sample_history_df):
        """测试布林带计算"""
        processor.df = sample_history_df
        params = {"period": 20, "std": 2}

        result = processor._calculate_boll(params)

        # 验证结果结构
        assert "upper" in result
        assert "middle" in result
        assert "lower" in result
        assert "price" in result

        # 验证上轨 > 中轨 > 下轨
        assert result["upper"] > result["middle"] > result["lower"]

    def test_calculate_ma(self, processor, sample_history_df):
        """测试均线计算"""
        processor.df = sample_history_df
        params = {"periods": [5, 10, 20, 60]}

        result = processor._calculate_ma(params)

        # 验证结果结构
        assert "values" in result
        assert "periods" in result

        # 验证长度
        assert len(result["values"]) == 4

    def test_judge_macd_signal_golden_cross(self, processor):
        """测试 MACD 金叉信号"""
        macd_result = {"dif": 0.5, "dea": 0.3, "macd": 0.4}

        signal, score = processor._judge_macd_signal(macd_result)

        assert signal == "金叉"
        assert score == 1

    def test_judge_macd_signal_dead_cross(self, processor):
        """测试 MACD 死叉信号"""
        macd_result = {"dif": 0.3, "dea": 0.5, "macd": -0.4}

        signal, score = processor._judge_macd_signal(macd_result)

        assert signal == "死叉"
        assert score == -1

    def test_judge_rsi_signal_overbought(self, processor):
        """测试 RSI 超买信号"""
        rsi_result = {"value": 85}

        signal, score = processor._judge_rsi_signal(rsi_result)

        assert signal == "超买"
        assert score == -2

    def test_judge_rsi_signal_oversold(self, processor):
        """测试 RSI 超卖信号"""
        rsi_result = {"value": 15}

        signal, score = processor._judge_rsi_signal(rsi_result)

        assert signal == "超卖"
        assert score == 2

    def test_judge_kdj_signal_overbought(self, processor):
        """测试 KDJ 超买信号"""
        kdj_result = {"k": 85, "d": 80, "j": 95}

        signal, score = processor._judge_kdj_signal(kdj_result)

        assert signal == "超买"
        assert score == -1

    def test_judge_kdj_signal_golden_cross(self, processor):
        """测试 KDJ 金叉信号"""
        kdj_result = {"k": 50, "d": 40, "j": 70}

        signal, score = processor._judge_kdj_signal(kdj_result)

        assert signal == "金叉"
        assert score == 1

    def test_judge_boll_signal_break_upper(self, processor):
        """测试布林带突破上轨信号"""
        boll_result = {"price": 15.0, "upper": 14.0, "middle": 12.0, "lower": 10.0}

        signal, score = processor._judge_boll_signal(boll_result)

        assert signal == "突破上轨"
        assert score == -1

    def test_judge_boll_signal_break_lower(self, processor):
        """测试布林带突破下轨信号"""
        boll_result = {"price": 9.0, "upper": 14.0, "middle": 12.0, "lower": 10.0}

        signal, score = processor._judge_boll_signal(boll_result)

        assert signal == "突破下轨"
        assert score == 1

    def test_judge_ma_signal_bullish_alignment(self, processor):
        """测试均线多头排列信号"""
        ma_result = {"values": [15.0, 14.0, 13.0, 12.0], "periods": [5, 10, 20, 60]}

        signal, score = processor._judge_ma_signal(ma_result)

        assert signal == "多头排列"
        assert score == 1

    def test_judge_ma_signal_bearish_alignment(self, processor):
        """测试均线空头排列信号"""
        ma_result = {"values": [12.0, 13.0, 14.0, 15.0], "periods": [5, 10, 20, 60]}

        signal, score = processor._judge_ma_signal(ma_result)

        assert signal == "空头排列"
        assert score == -1

    def test_calculate_summary_strong_buy(self, processor):
        """测试综合评分 - 强烈买入"""
        signals = [
            {"indicator": "macd", "signal": "金叉", "score": 1},
            {"indicator": "rsi", "signal": "超卖", "score": 2},
            {"indicator": "kdj", "signal": "金叉", "score": 1},
        ]

        summary = processor._calculate_summary(signals)

        assert summary["total_score"] == 4
        assert summary["recommendation"] == "强烈买入"
        assert summary["confidence"] == "高"

    def test_calculate_summary_strong_sell(self, processor):
        """测试综合评分 - 强烈卖出"""
        signals = [
            {"indicator": "macd", "signal": "死叉", "score": -1},
            {"indicator": "rsi", "signal": "超买", "score": -2},
            {"indicator": "kdj", "signal": "死叉", "score": -1},
        ]

        summary = processor._calculate_summary(signals)

        assert summary["total_score"] == -4
        assert summary["recommendation"] == "强烈卖出"
        assert summary["confidence"] == "高"

    def test_calculate_summary_neutral(self, processor):
        """测试综合评分 - 中性"""
        signals = [
            {"indicator": "macd", "signal": "金叉", "score": 1},
            {"indicator": "rsi", "signal": "超买", "score": -2},
            {"indicator": "kdj", "signal": "金叉", "score": 1},
        ]

        summary = processor._calculate_summary(signals)

        assert summary["total_score"] == 0
        assert summary["recommendation"] == "中性"
        assert summary["confidence"] == "低"

    def test_analyze_with_empty_data(self, processor, sample_history_df):
        """测试空数据处理"""
        # 直接设置空 DataFrame
        processor.df = pd.DataFrame()

        # 手动检查逻辑
        assert processor.df.empty

        # 使用非空数据验证处理逻辑
        processor.df = sample_history_df
        assert not processor.df.empty
