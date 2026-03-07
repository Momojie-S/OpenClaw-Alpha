# -*- coding: utf-8 -*-
"""期权情绪分析测试"""

import pytest

from skills.option_analysis.scripts.sentiment_processor.sentiment_processor import (
    judge_pcr_sentiment,
    judge_iv_level,
    generate_signal,
    get_exchange,
    UNDERLYING_NAMES
)


class TestPcrSentiment:
    """PCR 情绪判断测试"""

    def test_extremely_pessimistic(self):
        """极度悲观"""
        assert judge_pcr_sentiment(1.5) == "极度悲观"
        assert judge_pcr_sentiment(1.3) == "极度悲观"
        assert judge_pcr_sentiment(1.21) == "极度悲观"

    def test_pessimistic(self):
        """偏悲观"""
        assert judge_pcr_sentiment(1.1) == "偏悲观"
        assert judge_pcr_sentiment(1.05) == "偏悲观"

    def test_neutral(self):
        """中性"""
        assert judge_pcr_sentiment(0.8) == "中性"
        assert judge_pcr_sentiment(0.9) == "中性"
        assert judge_pcr_sentiment(1.0) == "中性"

    def test_optimistic(self):
        """偏乐观"""
        assert judge_pcr_sentiment(0.75) == "偏乐观"
        assert judge_pcr_sentiment(0.71) == "偏乐观"

    def test_extremely_optimistic(self):
        """极度乐观"""
        assert judge_pcr_sentiment(0.5) == "极度乐观"
        assert judge_pcr_sentiment(0.6) == "极度乐观"
        assert judge_pcr_sentiment(0.69) == "极度乐观"


class TestIvLevel:
    """波动率水平判断测试"""

    def test_high_volatility(self):
        """高波动"""
        assert judge_iv_level(35) == "高波动"
        assert judge_iv_level(40) == "高波动"
        assert judge_iv_level(30.1) == "高波动"

    def test_normal(self):
        """正常"""
        assert judge_iv_level(15) == "正常"
        assert judge_iv_level(20) == "正常"
        assert judge_iv_level(25) == "正常"
        assert judge_iv_level(29.9) == "正常"

    def test_low_volatility(self):
        """低波动"""
        assert judge_iv_level(10) == "低波动"
        assert judge_iv_level(14.9) == "低波动"
        assert judge_iv_level(5) == "低波动"


class TestSignalGeneration:
    """信号生成测试"""

    def test_extremely_pessimistic_signal(self):
        """极度悲观信号"""
        signal = generate_signal("极度悲观", "正常")
        assert "市场过度恐慌" in signal
        assert "可能反转向上" in signal

    def test_extremely_optimistic_signal(self):
        """极度乐观信号"""
        signal = generate_signal("极度乐观", "正常")
        assert "市场过度亢奋" in signal
        assert "可能反转向下" in signal

    def test_high_volatility_signal(self):
        """高波动信号"""
        signal = generate_signal("中性", "高波动")
        assert "波动率高企" in signal
        assert "可能接近底部" in signal

    def test_low_volatility_signal(self):
        """低波动信号"""
        signal = generate_signal("中性", "低波动")
        assert "波动率低位" in signal
        assert "可能即将变盘" in signal

    def test_stable_signal(self):
        """平稳信号"""
        signal = generate_signal("中性", "正常")
        assert "平稳" in signal

    def test_combined_signals(self):
        """组合信号"""
        signal = generate_signal("极度悲观", "高波动")
        assert "市场过度恐慌" in signal
        assert "波动率高企" in signal


class TestExchange:
    """交易所判断测试"""

    def test_sse_etf(self):
        """上交所 ETF"""
        assert get_exchange("510050") == "sse"
        assert get_exchange("510300") == "sse"
        assert get_exchange("588000") == "sse"

    def test_szse_etf(self):
        """深交所 ETF"""
        assert get_exchange("159919") == "szse"
        assert get_exchange("159915") == "szse"

    def test_index_option(self):
        """股指期权"""
        assert get_exchange("IO") == "cffex"
        assert get_exchange("HO") == "cffex"
        assert get_exchange("MO") == "cffex"


class TestUnderlyingNames:
    """标的名称映射测试"""

    def test_etf_names(self):
        """ETF 名称"""
        assert UNDERLYING_NAMES["510050"] == "50ETF"
        assert UNDERLYING_NAMES["510300"] == "300ETF"
        assert UNDERLYING_NAMES["159915"] == "创业板ETF"

    def test_index_names(self):
        """股指期权名称"""
        assert UNDERLYING_NAMES["IO"] == "沪深300股指"
        assert UNDERLYING_NAMES["HO"] == "上证50股指"
