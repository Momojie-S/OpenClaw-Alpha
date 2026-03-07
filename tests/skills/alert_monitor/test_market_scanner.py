# -*- coding: utf-8 -*-
"""市场扫描器测试"""

import pytest

from skills.alert_monitor.scripts.market_scanner import (
    MarketSignal,
    MarketScanResult,
    format_market_report,
)


class TestMarketSignal:
    """市场信号测试"""

    def test_create_signal(self):
        """测试创建市场信号"""
        signal = MarketSignal(
            type="北向大幅流入",
            level="中",
            detail="今日净流入 52.3 亿",
            data={"amount": 52.3},
        )

        assert signal.type == "北向大幅流入"
        assert signal.level == "中"
        assert signal.detail == "今日净流入 52.3 亿"
        assert signal.data == {"amount": 52.3}


class TestMarketScanResult:
    """市场扫描结果测试"""

    def test_create_result(self):
        """测试创建结果"""
        result = MarketScanResult(
            date="2026-03-08",
            signals=[
                MarketSignal(type="北向大幅流入", level="中", detail="净流入 50 亿"),
            ],
        )

        assert result.date == "2026-03-08"
        assert len(result.signals) == 1

    def test_to_dict(self):
        """测试转换为字典"""
        result = MarketScanResult(
            date="2026-03-08",
            signals=[],
        )

        data = result.to_dict()

        assert data["date"] == "2026-03-08"
        assert "signals" in data


class TestFormatMarketReport:
    """格式化市场报告测试"""

    def test_format_report_with_signals(self):
        """测试格式化有信号的报告"""
        result = MarketScanResult(
            date="2026-03-08",
            signals=[
                MarketSignal(type="北向大幅流入", level="中", detail="净流入 50 亿"),
                MarketSignal(type="板块热度急升", level="中", detail="电子: +35%"),
            ],
        )

        report = format_market_report(result)

        assert "2026-03-08" in report
        assert "北向大幅流入" in report
        assert "板块热度急升" in report

    def test_format_report_no_signals(self):
        """测试格式化无信号的报告"""
        result = MarketScanResult(
            date="2026-03-08",
            signals=[],
        )

        report = format_market_report(result)

        assert "2026-03-08" in report
        assert "无明显市场异动" in report
