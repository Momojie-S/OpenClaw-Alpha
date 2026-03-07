# -*- coding: utf-8 -*-
"""预警处理器测试"""

import pytest

from skills.alert_monitor.scripts.alert_processor import (
    AlertReport,
    format_alert_report,
)


class TestAlertReport:
    """预警报告测试"""

    def test_create_report(self):
        """测试创建报告"""
        report = AlertReport(
            date="2026-03-08",
            scan_type="full",
            has_high_risk=True,
            has_anomaly=True,
        )

        assert report.date == "2026-03-08"
        assert report.scan_type == "full"
        assert report.has_high_risk is True

    def test_to_dict(self):
        """测试转换为字典"""
        report = AlertReport(
            date="2026-03-08",
            scan_type="risk",
            risk_result={"total": 5},
        )

        data = report.to_dict()

        assert data["date"] == "2026-03-08"
        assert data["scan_type"] == "risk"
        assert data["risk_result"]["total"] == 5


class TestFormatAlertReport:
    """格式化预警报告测试"""

    def test_format_brief_report(self):
        """测试简报模式"""
        report = AlertReport(
            date="2026-03-08",
            scan_type="full",
            risk_result={
                "total": 10,
                "summary": {"high_risk": 1, "medium_risk": 2},
                "high_risk": [
                    {
                        "symbol": "002364",
                        "name": "中恒电气",
                        "signals": [{"detail": "业绩首亏"}],
                    }
                ],
                "medium_risk": [],
            },
            market_result={
                "signals": [
                    {"type": "北向大幅流入", "level": "中", "detail": "净流入 50 亿"}
                ]
            },
            has_high_risk=True,
            has_anomaly=True,
        )

        text = format_alert_report(report, brief=True)

        assert "2026-03-08" in text
        assert "高风险: 1 只" in text
        assert "002364" in text

    def test_format_full_report(self):
        """测试完整报告"""
        report = AlertReport(
            date="2026-03-08",
            scan_type="full",
            risk_result={
                "total": 5,
                "summary": {"high_risk": 0, "medium_risk": 1},
                "high_risk": [],
                "medium_risk": [
                    {
                        "symbol": "600000",
                        "name": "浦发银行",
                        "signals": [{"detail": "连续下跌 3 天"}],
                    }
                ],
            },
            market_result={"signals": []},
            has_high_risk=False,
            has_anomaly=False,
        )

        text = format_alert_report(report, brief=False)

        assert "2026-03-08" in text
        assert "600000" in text
        assert "连续下跌 3 天" in text

    def test_format_report_empty(self):
        """测试空报告"""
        report = AlertReport(
            date="2026-03-08",
            scan_type="full",
            risk_result=None,
            market_result={"signals": []},
        )

        text = format_alert_report(report)

        assert "2026-03-08" in text
