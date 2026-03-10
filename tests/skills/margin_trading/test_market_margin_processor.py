# -*- coding: utf-8 -*-
"""市场融资融券汇总 Processor 测试"""

import pytest
import pandas as pd

from openclaw_alpha.skills.margin_trading.market_margin_processor.market_margin_processor import (
    calculate_change_pct,
    get_latest_trading_day,
    format_text,
)


class TestCalculateChangePct:
    """测试 calculate_change_pct 函数"""

    def test_no_matching_date(self):
        """测试日期不存在"""
        df = pd.DataFrame({
            "日期": ["2026-03-06", "2026-03-07"],
            "融资余额": [100000, 101000],
        })
        result = calculate_change_pct(df, "2026-03-08")
        assert result == 0.0

    def test_first_day(self):
        """测试第一天无法计算环比"""
        df = pd.DataFrame({
            "日期": ["2026-03-08", "2026-03-09"],
            "融资余额": [100000, 101000],
        })
        result = calculate_change_pct(df, "2026-03-08")
        assert result == 0.0

    def test_normal_calculation(self):
        """测试正常计算环比"""
        df = pd.DataFrame({
            "日期": ["2026-03-06", "2026-03-07", "2026-03-08"],
            "融资余额": [100000, 101000, 102000],
        })
        result = calculate_change_pct(df, "2026-03-08")
        # (102000 - 101000) / 101000 * 100 ≈ 0.99
        assert abs(result - 0.99) < 0.01

    def test_zero_previous(self):
        """测试前一天数据为 0"""
        df = pd.DataFrame({
            "日期": ["2026-03-07", "2026-03-08"],
            "融资余额": [0, 100000],
        })
        result = calculate_change_pct(df, "2026-03-08")
        assert result == 0.0

    def test_negative_change(self):
        """测试负增长"""
        df = pd.DataFrame({
            "日期": ["2026-03-07", "2026-03-08"],
            "融资余额": [102000, 100000],
        })
        result = calculate_change_pct(df, "2026-03-08")
        # (100000 - 102000) / 102000 * 100 ≈ -1.96
        assert abs(result - (-1.96)) < 0.01


class TestGetLatestTradingDay:
    """测试 get_latest_trading_day 函数"""

    def test_get_latest(self):
        """测试获取最新交易日"""
        df = pd.DataFrame({
            "日期": ["2026-03-06", "2026-03-07", "2026-03-08"],
            "融资余额": [100000, 101000, 102000],
        })
        result = get_latest_trading_day(df)
        assert result == "2026-03-08"


class TestFormatText:
    """测试 format_text 函数"""

    def test_format_high_leverage(self):
        """测试高杠杆水平格式化"""
        data = {
            "date": "2026-03-08",
            "sh_market": {
                "financing_balance": 8500.5,
                "financing_buy": 500.2,
                "change_pct": 3.5,
            },
            "sz_market": {
                "financing_balance": 4500.3,
                "financing_buy": 300.1,
                "change_pct": 2.8,
            },
            "total": {
                "financing_balance": 13000.8,
                "avg_change_pct": 3.15,
            },
            "leverage_level": "高",
        }
        result = format_text(data)

        assert "高" in result
        assert "3.15%" in result
        assert "8500.5 亿" in result
        assert "4500.3 亿" in result
        assert "13000.8 亿" in result

    def test_format_low_leverage(self):
        """测试低杠杆水平格式化"""
        data = {
            "date": "2026-03-08",
            "sh_market": {
                "financing_balance": 8300.0,
                "financing_buy": 400.0,
                "change_pct": -2.5,
            },
            "sz_market": {
                "financing_balance": 4200.0,
                "financing_buy": 250.0,
                "change_pct": -3.0,
            },
            "total": {
                "financing_balance": 12500.0,
                "avg_change_pct": -2.75,
            },
            "leverage_level": "低",
        }
        result = format_text(data)

        assert "低" in result
        assert "-2.75%" in result

    def test_format_normal_leverage(self):
        """测试正常杠杆水平格式化"""
        data = {
            "date": "2026-03-08",
            "sh_market": {
                "financing_balance": 8400.0,
                "financing_buy": 450.0,
                "change_pct": 0.5,
            },
            "sz_market": {
                "financing_balance": 4300.0,
                "financing_buy": 280.0,
                "change_pct": -0.3,
            },
            "total": {
                "financing_balance": 12700.0,
                "avg_change_pct": 0.1,
            },
            "leverage_level": "正常",
        }
        result = format_text(data)

        assert "正常" in result
