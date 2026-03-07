# -*- coding: utf-8 -*-
"""PortfolioProcessor 测试"""

import pytest

from skills.portfolio_analysis.scripts.portfolio_processor.portfolio_processor import (
    PortfolioProcessor,
    Holding,
    IndustryDistribution,
    RiskAlert,
    PortfolioResult,
)


class TestParseHoldingsString:
    """测试持仓字符串解析"""

    def test_parse_simple(self):
        """测试简单格式（无成本价）"""
        processor = PortfolioProcessor()
        result = processor.parse_holdings_string("000001:1000,600000:500")

        assert len(result) == 2
        assert result[0] == {"code": "000001", "shares": 1000, "cost": None}
        assert result[1] == {"code": "600000", "shares": 500, "cost": None}

    def test_parse_with_cost(self):
        """测试完整格式（含成本价）"""
        processor = PortfolioProcessor()
        result = processor.parse_holdings_string("000001:1000:12.5,600000:500:8.2")

        assert len(result) == 2
        assert result[0] == {"code": "000001", "shares": 1000, "cost": 12.5}
        assert result[1] == {"code": "600000", "shares": 500, "cost": 8.2}

    def test_parse_mixed(self):
        """测试混合格式"""
        processor = PortfolioProcessor()
        result = processor.parse_holdings_string("000001:1000:12.5,600000:500")

        assert len(result) == 2
        assert result[0]["cost"] == 12.5
        assert result[1]["cost"] is None

    def test_parse_empty(self):
        """测试空字符串"""
        processor = PortfolioProcessor()
        result = processor.parse_holdings_string("")
        assert result == []

    def test_parse_invalid(self):
        """测试无效格式"""
        processor = PortfolioProcessor()
        result = processor.parse_holdings_string("invalid,000001:1000")
        assert len(result) == 1
        assert result[0]["code"] == "000001"


class TestCalculateWeights:
    """测试权重计算"""

    def test_basic_weights(self):
        """测试基本权重计算"""
        processor = PortfolioProcessor()
        holdings_input = [
            {"code": "000001", "shares": 1000, "cost": None},
            {"code": "600000", "shares": 500, "cost": None},
        ]
        stock_data = {
            "000001": {"price": 10.0, "name": "平安银行", "change_pct": 0, "industry": "银行"},
            "600000": {"price": 10.0, "name": "浦发银行", "change_pct": 0, "industry": "银行"},
        }

        result = processor.calculate_weights(holdings_input, stock_data)

        assert len(result) == 2
        # 总市值 = 10000 + 5000 = 15000
        # 权重: 66.67% 和 33.33%
        assert result[0].market_value == 10000.0
        assert result[1].market_value == 5000.0
        assert result[0].weight == pytest.approx(66.67, rel=0.01)
        assert result[1].weight == pytest.approx(33.33, rel=0.01)

    def test_profit_calculation(self):
        """测试盈亏计算"""
        processor = PortfolioProcessor()
        holdings_input = [
            {"code": "000001", "shares": 1000, "cost": 10.0},
        ]
        stock_data = {
            "000001": {"price": 12.0, "name": "平安银行", "change_pct": 0, "industry": "银行"},
        }

        result = processor.calculate_weights(holdings_input, stock_data)

        assert len(result) == 1
        assert result[0].profit == 2000.0  # (12-10) * 1000
        assert result[0].profit_pct == 20.0  # (12-10)/10 * 100

    def test_missing_stock_data(self):
        """测试缺失股票数据"""
        processor = PortfolioProcessor()
        holdings_input = [
            {"code": "999999", "shares": 1000, "cost": None},
        ]
        stock_data = {}

        result = processor.calculate_weights(holdings_input, stock_data)

        assert len(result) == 1
        assert result[0].price == 0
        assert result[0].market_value == 0


class TestIndustryDistribution:
    """测试行业分布计算"""

    def test_single_industry(self):
        """测试单一行业"""
        processor = PortfolioProcessor()
        holdings = [
            Holding(code="000001", name="A", shares=1000, price=10, market_value=10000, weight=50, industry="银行"),
            Holding(code="600000", name="B", shares=500, price=20, market_value=10000, weight=50, industry="银行"),
        ]

        result = processor.calculate_industry_distribution(holdings)

        assert len(result) == 1
        assert result[0].industry == "银行"
        assert result[0].weight == 100.0
        assert result[0].count == 2

    def test_multiple_industries(self):
        """测试多行业"""
        processor = PortfolioProcessor()
        holdings = [
            Holding(code="000001", name="A", shares=1000, price=10, market_value=10000, weight=50, industry="银行"),
            Holding(code="002475", name="B", shares=500, price=20, market_value=10000, weight=50, industry="电子"),
        ]

        result = processor.calculate_industry_distribution(holdings)

        assert len(result) == 2
        # 按权重排序
        assert result[0].weight == 50.0
        assert result[1].weight == 50.0


class TestHHI:
    """测试集中度指数计算"""

    def test_concentrated(self):
        """测试高度集中"""
        processor = PortfolioProcessor()
        holdings = [
            Holding(code="000001", name="A", shares=1000, price=10, market_value=10000, weight=80, industry="银行"),
            Holding(code="600000", name="B", shares=500, price=10, market_value=2500, weight=20, industry="银行"),
        ]

        hhi = processor.calculate_hhi(holdings)

        # HHI = 80^2 + 20^2 = 6400 + 400 = 6800
        assert hhi == 6800.0

    def test_diversified(self):
        """测试分散"""
        processor = PortfolioProcessor()
        holdings = [
            Holding(code=f"{i:06d}", name=f"Stock{i}", shares=100, price=10, market_value=1000, weight=10, industry="银行")
            for i in range(10)
        ]

        hhi = processor.calculate_hhi(holdings)

        # HHI = 10 * 10^2 = 1000
        assert hhi == 1000.0


class TestRiskCheck:
    """测试风险检查"""

    def test_stock_concentration(self):
        """测试单股集中风险"""
        processor = PortfolioProcessor()
        holdings = [
            Holding(code="000001", name="A", shares=1000, price=10, market_value=35000, weight=35, industry="银行"),
            Holding(code="600000", name="B", shares=500, price=10, market_value=15000, weight=15, industry="银行"),
        ]
        industry_dist = [
            IndustryDistribution(industry="银行", weight=100, market_value=50000, count=2),
        ]

        alerts = processor.check_risks(holdings, industry_dist)

        # 应该有单股集中风险
        stock_alerts = [a for a in alerts if a.type == "单股集中"]
        assert len(stock_alerts) == 1
        assert stock_alerts[0].level == "high"

    def test_industry_concentration(self):
        """测试行业集中风险"""
        processor = PortfolioProcessor()
        holdings = [
            Holding(code="000001", name="A", shares=1000, price=10, market_value=30000, weight=30, industry="银行"),
            Holding(code="600000", name="B", shares=500, price=10, market_value=25000, weight=25, industry="银行"),
            Holding(code="002475", name="C", shares=500, price=10, market_value=25000, weight=25, industry="银行"),
        ]
        industry_dist = [
            IndustryDistribution(industry="银行", weight=80, market_value=80000, count=3),
        ]

        alerts = processor.check_risks(holdings, industry_dist)

        # 应该有行业集中风险
        industry_alerts = [a for a in alerts if a.type == "行业集中"]
        assert len(industry_alerts) == 1
        assert industry_alerts[0].level == "high"

    def test_few_holdings(self):
        """测试持仓过少风险"""
        processor = PortfolioProcessor()
        holdings = [
            Holding(code="000001", name="A", shares=1000, price=10, market_value=50000, weight=50, industry="银行"),
            Holding(code="600000", name="B", shares=500, price=10, market_value=50000, weight=50, industry="电子"),
        ]
        industry_dist = [
            IndustryDistribution(industry="银行", weight=50, market_value=50000, count=1),
            IndustryDistribution(industry="电子", weight=50, market_value=50000, count=1),
        ]

        alerts = processor.check_risks(holdings, industry_dist)

        # 应该有持仓过少风险
        few_alerts = [a for a in alerts if a.type == "持仓过少"]
        assert len(few_alerts) == 1
        assert few_alerts[0].level == "medium"

    def test_many_holdings(self):
        """测试持仓过多风险"""
        processor = PortfolioProcessor()
        holdings = [
            Holding(code=f"{i:06d}", name=f"S{i}", shares=100, price=10, market_value=1000, weight=4.5, industry="银行")
            for i in range(25)
        ]
        industry_dist = [
            IndustryDistribution(industry="银行", weight=100, market_value=25000, count=25),
        ]

        alerts = processor.check_risks(holdings, industry_dist)

        # 应该有持仓过多风险
        many_alerts = [a for a in alerts if a.type == "持仓过多"]
        assert len(many_alerts) == 1
        assert many_alerts[0].level == "low"


class TestProcess:
    """测试完整处理流程"""

    def test_full_process(self):
        """测试完整处理"""
        processor = PortfolioProcessor()
        holdings_input = [
            {"code": "000001", "shares": 1000, "cost": 10.0},
            {"code": "600000", "shares": 500, "cost": 8.0},
        ]
        stock_data = {
            "000001": {"price": 12.0, "name": "平安银行", "change_pct": 2.0, "industry": "银行"},
            "600000": {"price": 10.0, "name": "浦发银行", "change_pct": 1.0, "industry": "银行"},
        }

        result = processor.process(holdings_input, stock_data)

        assert isinstance(result, PortfolioResult)
        assert result.total_value == 17000.0  # 12000 + 5000
        assert result.total_cost == 14000.0  # 10000 + 4000
        assert result.total_profit == 3000.0
        assert len(result.holdings) == 2
        assert len(result.industry_distribution) >= 1
        assert result.hhi > 0

    def test_format_summary(self):
        """测试格式化摘要"""
        processor = PortfolioProcessor()
        holdings_input = [{"code": "000001", "shares": 1000, "cost": 10.0}]
        stock_data = {
            "000001": {"price": 12.0, "name": "平安银行", "change_pct": 2.0, "industry": "银行"},
        }

        result = processor.process(holdings_input, stock_data)
        summary = processor.format_summary(result)

        assert "持仓分析报告" in summary
        assert "平安银行" in summary
        assert "¥12,000" in summary

    def test_to_dict(self):
        """测试转换为字典"""
        processor = PortfolioProcessor()
        holdings_input = [{"code": "000001", "shares": 1000, "cost": 10.0}]
        stock_data = {
            "000001": {"price": 12.0, "name": "平安银行", "change_pct": 2.0, "industry": "银行"},
        }

        result = processor.process(holdings_input, stock_data)
        result_dict = processor.to_dict(result)

        assert "summary" in result_dict
        assert "holdings" in result_dict
        assert "industry_distribution" in result_dict
        assert "risk_alerts" in result_dict
        assert result_dict["summary"]["total_value"] == 12000.0
