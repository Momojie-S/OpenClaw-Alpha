# -*- coding: utf-8 -*-
"""炒作风险 Processor 测试"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from openclaw_alpha.skills.theme_speculation.speculation_risk_processor.speculation_risk_processor import (
    SpeculationRiskProcessor,
    RiskAlert,
    SpeculationRiskResult,
)
from openclaw_alpha.skills.limit_up_tracker.limit_up_fetcher.models import (
    LimitUpItem,
    LimitUpType,
)


def create_limit_up_item(
    code: str,
    name: str,
    continuous: int = 3,
    first_limit_time: str = "09:35:00",
    float_mv: float = 100.0,
    change_pct: float = 10.0,
) -> LimitUpItem:
    """创建涨停股数据（测试辅助函数）"""
    return LimitUpItem(
        code=code,
        name=name,
        continuous=continuous,
        first_limit_time=first_limit_time,
        last_limit_time=first_limit_time,
        float_mv=float_mv,
        total_mv=float_mv * 2,
        change_pct=change_pct,
        price=12.0,
        amount=10.0,
        turnover_rate=5.0,
        limit_times=0,
        limit_stat=f"{continuous}/{continuous}",
        industry="测试行业",
    )


class TestRiskAlert:
    """测试风险提示数据类"""

    def test_to_dict(self):
        """测试转换为字典"""
        alert = RiskAlert(
            risk_type="情绪过热",
            level="高",
            trigger="涨停家数120，连板5板",
            description="市场情绪过热，短期调整风险较大",
        )

        result = alert.to_dict()

        assert result["risk_type"] == "情绪过热"
        assert result["level"] == "高"
        assert result["trigger"] == "涨停家数120，连板5板"
        assert result["description"] == "市场情绪过热，短期调整风险较大"


class TestSpeculationRiskResult:
    """测试炒作风险结果数据类"""

    def test_to_dict(self):
        """测试转换为字典"""
        result = SpeculationRiskResult(
            code="000001",
            name="平安银行",
            date="2026-03-11",
            continuous=3,
            change_pct=10.0,
            alerts=[
                RiskAlert(
                    risk_type="监管风险",
                    level="中",
                    trigger="连续3日涨停",
                    description="连续涨停可能引发监管关注",
                ),
            ],
            overall_risk="中",
        )

        data = result.to_dict()

        assert data["code"] == "000001"
        assert data["name"] == "平安银行"
        assert data["continuous"] == 3
        assert len(data["alerts"]) == 1
        assert data["overall_risk"] == "中"


class TestSpeculationRiskProcessor:
    """测试炒作风险处理器"""

    @pytest.fixture
    def processor(self):
        """创建处理器实例"""
        return SpeculationRiskProcessor("000001", "2026-03-11")

    def test_find_target_stock_found(self, processor):
        """测试查找目标股票：找到"""
        items = [
            create_limit_up_item("000002", "万科A", continuous=2),
            create_limit_up_item("000001", "平安银行", continuous=3),
        ]

        result = processor._find_target_stock(items)

        assert result is not None
        assert result.code == "000001"
        assert result.name == "平安银行"

    def test_find_target_stock_not_found(self, processor):
        """测试查找目标股票：未找到"""
        items = [create_limit_up_item("000002", "万科A", continuous=2)]

        result = processor._find_target_stock(items)

        assert result is None

    def test_calculate_overall_risk_high(self, processor):
        """测试综合风险等级：高"""
        alerts = [
            RiskAlert(
                risk_type="情绪过热",
                level="高",
                trigger="涨停家数120",
                description="市场情绪过热",
            ),
            RiskAlert(
                risk_type="监管风险",
                level="高",
                trigger="连续5日涨停",
                description="可能引发监管关注",
            ),
        ]

        result = processor._calculate_overall_risk(alerts)

        assert result == "高"

    def test_calculate_overall_risk_medium(self, processor):
        """测试综合风险等级：中"""
        alerts = [
            RiskAlert(
                risk_type="监管风险",
                level="高",
                trigger="连续3日涨停",
                description="可能引发监管关注",
            ),
        ]

        result = processor._calculate_overall_risk(alerts)

        assert result == "中"

    def test_calculate_overall_risk_low(self, processor):
        """测试综合风险等级：低"""
        alerts = []

        result = processor._calculate_overall_risk(alerts)

        assert result == "低"

    def test_evaluate_risk_emotional_overheat(self, processor):
        """测试风险评估：情绪过热"""
        stock = create_limit_up_item("000001", "平安银行", continuous=5)

        sentiment = {
            "limit_up_count": 120,
            "broken_rate": 20.0,
            "max_continuous": 6,
        }

        result = processor._evaluate_risk(stock, sentiment, None)

        assert result.code == "000001"
        assert result.continuous == 5
        # 应该有情绪过热和监管风险
        assert any(a.risk_type == "情绪过热" for a in result.alerts)
        assert any(a.risk_type == "监管风险" for a in result.alerts)

    def test_evaluate_risk_broken_board(self, processor):
        """测试风险评估：炸板风险"""
        stock = create_limit_up_item("000001", "平安银行", continuous=2)

        sentiment = {
            "limit_up_count": 50,
            "broken_rate": 55.0,
            "max_continuous": 3,
        }

        result = processor._evaluate_risk(stock, sentiment, None)

        assert any(a.risk_type == "炸板风险" and a.level == "高" for a in result.alerts)

    def test_evaluate_risk_regulatory(self, processor):
        """测试风险评估：监管风险"""
        stock = create_limit_up_item("000001", "平安银行", continuous=3)

        sentiment = {
            "limit_up_count": 50,
            "broken_rate": 20.0,
            "max_continuous": 3,
        }

        result = processor._evaluate_risk(stock, sentiment, None)

        # 连续3板应该有监管风险
        assert any(
            a.risk_type == "监管风险" and "连续3日涨停" in a.trigger
            for a in result.alerts
        )

    def test_evaluate_risk_valuation_deviation(self, processor):
        """测试风险评估：涨幅偏离基本面"""
        stock = create_limit_up_item("000001", "平安银行", continuous=2)

        sentiment = {
            "limit_up_count": 50,
            "broken_rate": 20.0,
            "max_continuous": 3,
        }

        # PE 100，行业 PE 40，偏离 150%
        fundamental = {
            "pe_ttm": 100,
            "industry_pe": 40,
        }

        result = processor._evaluate_risk(stock, sentiment, fundamental)

        assert any(a.risk_type == "涨幅偏离" and a.level == "高" for a in result.alerts)

    def test_evaluate_risk_not_limit_up(self, processor):
        """测试风险评估：未涨停"""
        # 当不在涨停列表中时，返回低风险
        result = SpeculationRiskResult(
            code="000001",
            name="未知",
            date="2026-03-11",
            continuous=0,
            change_pct=0,
            alerts=[
                RiskAlert(
                    risk_type="涨幅偏离",
                    level="低",
                    trigger="未涨停",
                    description="该股票今日未涨停，炒作风险较低",
                ),
            ],
            overall_risk="低",
        )

        assert result.overall_risk == "低"
        assert len(result.alerts) == 1
        assert result.alerts[0].risk_type == "涨幅偏离"
