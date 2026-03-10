# -*- coding: utf-8 -*-
"""财务健康评分测试"""

import pytest

from openclaw_alpha.skills.fundamental_analysis.fundamental_processor.fundamental_processor import (
    _rate_debt_ratio_score,
    _rate_current_ratio_score,
    _rate_cash_flow_score,
    _calc_financial_health_score,
)


class TestDebtRatioScore:
    """资产负债率评分测试"""

    def test_low_debt(self):
        """低负债：健康"""
        score = _rate_debt_ratio_score(30, "测试公司")
        assert score == 100

    def test_normal_debt(self):
        """正常负债"""
        score = _rate_debt_ratio_score(50, "测试公司")
        assert score == 70

    def test_high_debt(self):
        """高负债：关注"""
        score = _rate_debt_ratio_score(65, "测试公司")
        assert score == 40

    def test_dangerous_debt(self):
        """危险负债"""
        score = _rate_debt_ratio_score(80, "测试公司")
        assert score == 10

    def test_financial_company(self):
        """金融行业特殊处理"""
        score = _rate_debt_ratio_score(92, "平安银行")
        assert score == 70  # 金融行业正常

    def test_financial_company_high(self):
        """金融行业超高负债"""
        score = _rate_debt_ratio_score(96, "平安银行")
        assert score == 40  # 金融行业关注

    def test_none_debt(self):
        """无数据"""
        score = _rate_debt_ratio_score(None, "测试公司")
        assert score == 50


class TestCurrentRatioScore:
    """流动比率评分测试"""

    def test_excellent_liquidity(self):
        """优秀流动性"""
        score = _rate_current_ratio_score(2.5)
        assert score == 100

    def test_good_liquidity(self):
        """良好流动性"""
        score = _rate_current_ratio_score(1.8)
        assert score == 80

    def test_average_liquidity(self):
        """一般流动性"""
        score = _rate_current_ratio_score(1.2)
        assert score == 50

    def test_poor_liquidity(self):
        """流动性差"""
        score = _rate_current_ratio_score(0.8)
        assert score == 10

    def test_none_liquidity(self):
        """无数据"""
        score = _rate_current_ratio_score(None)
        assert score == 50


class TestCashFlowScore:
    """现金流评分测试"""

    def test_positive_cash_flow(self):
        """正现金流"""
        score = _rate_cash_flow_score(1.5)
        assert score == 70

    def test_negative_cash_flow(self):
        """负现金流"""
        score = _rate_cash_flow_score(-0.5)
        assert score == 10

    def test_zero_cash_flow(self):
        """零现金流"""
        score = _rate_cash_flow_score(0)
        assert score == 10  # 零或负都是风险

    def test_none_cash_flow(self):
        """无数据"""
        score = _rate_cash_flow_score(None)
        assert score == 50


class TestCalcFinancialHealthScore:
    """财务健康综合评分测试"""

    def test_healthy_company(self):
        """健康公司：低负债 + 高流动性 + 正现金流"""
        result = _calc_financial_health_score(
            debt_ratio=30,
            current_ratio=2.5,
            cash_per_share=1.5,
            name="测试公司",
        )
        # 100*0.4 + 100*0.3 + 70*0.3 = 40 + 30 + 21 = 91
        assert result["score"] == 91.0
        assert result["rating"] == "健康"
        assert result["details"]["debt_score"] == 100
        assert result["details"]["liquidity_score"] == 100
        assert result["details"]["cash_flow_score"] == 70

    def test_normal_company(self):
        """正常公司：正常负债 + 一般流动性 + 正现金流"""
        result = _calc_financial_health_score(
            debt_ratio=50,
            current_ratio=1.2,
            cash_per_share=0.5,
            name="测试公司",
        )
        # 70*0.4 + 50*0.3 + 70*0.3 = 28 + 15 + 21 = 64
        assert result["score"] == 64.0
        assert result["rating"] == "正常"

    def test_concern_company(self):
        """关注公司：高负债 + 差流动性 + 负现金流"""
        result = _calc_financial_health_score(
            debt_ratio=65,
            current_ratio=0.8,
            cash_per_share=-0.5,
            name="测试公司",
        )
        # 40*0.4 + 10*0.3 + 10*0.3 = 16 + 3 + 3 = 22
        assert result["score"] == 22.0
        assert result["rating"] == "风险"

    def test_financial_company(self):
        """金融公司：高负债（正常）+ 无流动性数据"""
        result = _calc_financial_health_score(
            debt_ratio=92,
            current_ratio=None,
            cash_per_share=2.0,
            name="平安银行",
        )
        # 70*0.4 + 50*0.3 + 70*0.3 = 28 + 15 + 21 = 64
        assert result["score"] == 64.0
        assert result["rating"] == "正常"

    def test_partial_data(self):
        """部分数据缺失"""
        result = _calc_financial_health_score(
            debt_ratio=None,
            current_ratio=None,
            cash_per_share=None,
            name="测试公司",
        )
        # 50*0.4 + 50*0.3 + 50*0.3 = 50
        assert result["score"] == 50.0
        assert result["rating"] == "关注"
