# -*- coding: utf-8 -*-
"""风险扫描器测试"""

from unittest.mock import AsyncMock, patch

import pytest

from openclaw_alpha.skills.alert_monitor.risk_scanner import (
    RiskSignal,
    StockRiskReport,
    RiskScanResult,
    format_risk_report,
)
from openclaw_alpha.skills.alert_monitor.config_parser import AlertConfig, WatchlistItem


class TestRiskSignal:
    """风险信号测试"""

    def test_create_risk_signal(self):
        """测试创建风险信号"""
        signal = RiskSignal(
            type="业绩风险",
            level="高",
            detail="业绩首亏，预计变动 -336.7%",
            suggestion="关注公告详情",
        )

        assert signal.type == "业绩风险"
        assert signal.level == "高"
        assert signal.detail == "业绩首亏，预计变动 -336.7%"


class TestStockRiskReport:
    """股票风险报告测试"""

    def test_create_report(self):
        """测试创建报告"""
        report = StockRiskReport(
            symbol="002364",
            name="中恒电气",
            rating="高风险",
            signals=[
                RiskSignal(type="业绩风险", level="高", detail="业绩首亏"),
            ],
        )

        assert report.symbol == "002364"
        assert report.rating == "高风险"
        assert len(report.signals) == 1


class TestRiskScanResult:
    """风险扫描结果测试"""

    def test_create_result(self):
        """测试创建结果"""
        result = RiskScanResult(
            date="2026-03-08",
            total=10,
            high_risk=[
                StockRiskReport(symbol="002364", name="中恒电气", rating="高风险"),
            ],
            medium_risk=[
                StockRiskReport(symbol="600000", name="浦发银行", rating="中风险"),
            ],
        )

        assert result.date == "2026-03-08"
        assert result.total == 10
        assert len(result.high_risk) == 1
        assert len(result.medium_risk) == 1

    def test_to_dict(self):
        """测试转换为字典"""
        result = RiskScanResult(
            date="2026-03-08",
            total=5,
            high_risk=[],
            medium_risk=[],
            low_risk=[],
            normal=[],
        )

        data = result.to_dict()

        assert data["date"] == "2026-03-08"
        assert data["total"] == 5
        assert "summary" in data


class TestFormatRiskReport:
    """格式化风险报告测试"""

    def test_format_report_with_risks(self):
        """测试格式化有风险的报告"""
        result = RiskScanResult(
            date="2026-03-08",
            total=10,
            high_risk=[
                StockRiskReport(
                    symbol="002364",
                    name="中恒电气",
                    rating="高风险",
                    signals=[
                        RiskSignal(type="业绩风险", level="高", detail="业绩首亏"),
                    ],
                ),
            ],
            medium_risk=[
                StockRiskReport(
                    symbol="600000",
                    name="浦发银行",
                    rating="中风险",
                    signals=[
                        RiskSignal(type="价格风险", level="中", detail="连续下跌 3 天"),
                    ],
                ),
            ],
            low_risk=[],
            normal=[],
        )

        report = format_risk_report(result)

        assert "2026-03-08" in report
        assert "高风险: 1 只" in report
        assert "中风险: 1 只" in report
        assert "002364" in report
        assert "600000" in report

    def test_format_report_no_risks(self):
        """测试格式化无风险的报告"""
        result = RiskScanResult(
            date="2026-03-08",
            total=5,
            high_risk=[],
            medium_risk=[],
            low_risk=[],
            normal=[
                StockRiskReport(symbol="000001", name="平安银行", rating="正常"),
            ],
        )

        report = format_risk_report(result)

        assert "2026-03-08" in report
        assert "高风险: 0 只" in report
