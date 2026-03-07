# -*- coding: utf-8 -*-
"""综合评分测试"""

import pytest

from skills.fundamental_analysis.scripts.fundamental_processor.fundamental_processor import (
    _calc_overall_score,
)


class TestCalcOverallScore:
    """综合评分计算测试"""

    def test_excellent_company(self):
        """优秀公司：低估 + 高ROE + 高增长 + 健康财务"""
        data = {
            "valuation": {"pe_rating": "低估", "pb_rating": "低估"},
            "profitability": {"roe_rating": "优秀"},
            "growth": {"growth_rating": "高增长"},
            "financial_health": {"debt_rating": "健康"},
        }
        result = _calc_overall_score(data)
        assert result["score"] >= 80
        assert result["rating"] == "优秀"
        assert result["details"]["valuation"] == 100
        assert result["details"]["profitability"] == 100
        assert result["details"]["growth"] == 100
        assert result["details"]["financial_health"] == 100

    def test_good_company(self):
        """良好公司：合理估值 + 良好ROE + 稳定增长"""
        data = {
            "valuation": {"pe_rating": "合理", "pb_rating": "合理"},
            "profitability": {"roe_rating": "良好"},
            "growth": {"growth_rating": "稳定增长"},
            "financial_health": {"debt_rating": "正常"},
        }
        result = _calc_overall_score(data)
        assert 65 <= result["score"] < 80
        assert result["rating"] == "良好"

    def test_average_company(self):
        """一般公司：估值合理 + ROE 一般 + 下滑"""
        data = {
            "valuation": {"pe_rating": "合理", "pb_rating": "低估"},
            "profitability": {"roe_rating": "一般"},
            "growth": {"growth_rating": "下滑"},
            "financial_health": {"debt_rating": "正常"},
        }
        result = _calc_overall_score(data)
        assert 50 <= result["score"] < 65
        assert result["rating"] == "一般"

    def test_poor_company(self):
        """较差公司：高估 + ROE 较差 + 下滑（不是大幅下滑）"""
        data = {
            "valuation": {"pe_rating": "高估", "pb_rating": "合理"},  # 55
            "profitability": {"roe_rating": "较差"},  # 20
            "growth": {"growth_rating": "下滑"},  # 40
            "financial_health": {"debt_rating": "关注"},  # 40
        }
        result = _calc_overall_score(data)
        # 55*0.25 + 20*0.30 + 40*0.25 + 40*0.20 = 13.75 + 6 + 10 + 8 = 37.75
        assert 35 <= result["score"] < 50
        assert result["rating"] == "较差"

    def test_dangerous_company(self):
        """危险公司：高估 + 较差ROE + 大幅下滑 + 风险财务"""
        data = {
            "valuation": {"pe_rating": "高估", "pb_rating": "高估"},
            "profitability": {"roe_rating": "较差"},
            "growth": {"growth_rating": "大幅下滑"},
            "financial_health": {"debt_rating": "风险"},
        }
        result = _calc_overall_score(data)
        assert result["score"] < 35
        assert result["rating"] == "危险"

    def test_missing_data(self):
        """缺少数据时使用默认值"""
        data = {
            "valuation": {"pe_rating": None, "pb_rating": None},
            "profitability": {"roe_rating": "未知"},
            "growth": {"growth_rating": "未知"},
            "financial_health": {"debt_rating": "未知"},
        }
        result = _calc_overall_score(data)
        assert result["score"] == 50.0
        assert result["rating"] == "一般"

    def test_partial_valuation(self):
        """部分估值数据（只有 PE）"""
        data = {
            "valuation": {"pe_rating": "低估", "pb_rating": None},
            "profitability": {"roe_rating": "良好"},
            "growth": {"growth_rating": "稳定增长"},
            "financial_health": {"debt_rating": "正常"},
        }
        result = _calc_overall_score(data)
        # 只有 PE 低估 = 100，其他正常
        assert result["details"]["valuation"] == 100
