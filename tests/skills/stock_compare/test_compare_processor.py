# -*- coding: utf-8 -*-
"""个股对比分析处理器测试"""

import pytest

from openclaw_alpha.skills.stock_compare.compare_processor import (
    StockMetrics,
    StockScore,
    CompareResult,
    calculate_scores,
    format_compare_result,
)


class TestStockMetrics:
    """股票指标测试"""

    def test_create_metrics(self):
        """测试创建指标"""
        metrics = StockMetrics(
            code="000001",
            name="平安银行",
            price=12.50,
            change_pct=2.35,
            turnover_rate=1.23,
            amount=10.5,
            market_cap=2425.5,
            pe=8.5,
            pb=0.9,
        )

        assert metrics.code == "000001"
        assert metrics.name == "平安银行"
        assert metrics.price == 12.50
        assert metrics.pe == 8.5


class TestStockScore:
    """股票评分测试"""

    def test_create_score(self):
        """测试创建评分"""
        score = StockScore(
            code="000001",
            name="平安银行",
            total_score=75.5,
            valuation_score=90.0,
            momentum_score=61.8,
            liquidity_score=50.0,
            fund_score=50.0,
            rank=1,
        )

        assert score.code == "000001"
        assert score.total_score == 75.5
        assert score.rank == 1


class TestCalculateScores:
    """评分计算测试"""

    def test_calculate_single_stock(self):
        """测试计算单只股票评分"""
        metrics = [
            StockMetrics(
                code="000001",
                name="平安银行",
                price=12.50,
                change_pct=2.0,
                turnover_rate=5.0,
                amount=10.0,
                market_cap=2400.0,
                pe=10.0,  # PE < 15, 估值得分 90
            )
        ]

        scores = calculate_scores(metrics)

        assert len(scores) == 1
        assert scores[0].code == "000001"
        assert scores[0].valuation_score == 90  # PE < 15
        assert scores[0].momentum_score == 60  # 50 + 2*5
        assert scores[0].liquidity_score == 80  # 换手率 3-8%
        assert scores[0].rank == 1

    def test_calculate_multiple_stocks_ranking(self):
        """测试多只股票排名"""
        metrics = [
            StockMetrics(
                code="000001",
                name="平安银行",
                price=12.50,
                change_pct=3.0,  # 高动量
                turnover_rate=5.0,
                amount=10.0,
                market_cap=2400.0,
                pe=10.0,  # 低 PE
            ),
            StockMetrics(
                code="600000",
                name="浦发银行",
                price=9.80,
                change_pct=1.0,  # 低动量
                turnover_rate=2.0,  # 低换手
                amount=8.0,
                market_cap=2800.0,
                pe=30.0,  # 高 PE
            ),
        ]

        scores = calculate_scores(metrics)

        assert len(scores) == 2
        # 第一只应该排名更高
        assert scores[0].code == "000001"
        assert scores[0].rank == 1
        assert scores[1].code == "600000"
        assert scores[1].rank == 2

    def test_valuation_score_levels(self):
        """测试估值得分等级"""
        # PE < 15
        m1 = StockMetrics(
            code="001", name="", price=10, change_pct=0, turnover_rate=5,
            amount=1, market_cap=100, pe=10
        )
        # 15 <= PE < 30
        m2 = StockMetrics(
            code="002", name="", price=10, change_pct=0, turnover_rate=5,
            amount=1, market_cap=100, pe=20
        )
        # 30 <= PE < 50
        m3 = StockMetrics(
            code="003", name="", price=10, change_pct=0, turnover_rate=5,
            amount=1, market_cap=100, pe=40
        )
        # PE >= 50
        m4 = StockMetrics(
            code="004", name="", price=10, change_pct=0, turnover_rate=5,
            amount=1, market_cap=100, pe=60
        )

        scores = calculate_scores([m1, m2, m3, m4])

        assert scores[0].valuation_score == 90  # PE < 15
        assert scores[1].valuation_score == 70  # 15-30
        assert scores[2].valuation_score == 50  # 30-50
        assert scores[3].valuation_score == 30  # >= 50

    def test_liquidity_score_levels(self):
        """测试流动性得分等级"""
        # 换手率 3-8%
        m1 = StockMetrics(
            code="001", name="", price=10, change_pct=0, turnover_rate=5,
            amount=1, market_cap=100, pe=20
        )
        # 换手率 < 3%
        m2 = StockMetrics(
            code="002", name="", price=10, change_pct=0, turnover_rate=1,
            amount=1, market_cap=100, pe=20
        )
        # 换手率 > 8%
        m3 = StockMetrics(
            code="003", name="", price=10, change_pct=0, turnover_rate=15,
            amount=1, market_cap=100, pe=20
        )

        scores = calculate_scores([m1, m2, m3])

        assert scores[0].liquidity_score == 80  # 3-8%
        assert scores[1].liquidity_score == 50  # < 3%
        assert scores[2].liquidity_score < 80  # > 8%


class TestCompareResult:
    """对比结果测试"""

    def test_create_result(self):
        """测试创建结果"""
        result = CompareResult(
            date="2026-03-08",
            stocks=[
                StockMetrics(
                    code="000001", name="平安银行", price=12.50,
                    change_pct=2.0, turnover_rate=5.0, amount=10.0,
                    market_cap=2400.0
                )
            ],
            scores=[
                StockScore(
                    code="000001", name="平安银行", total_score=75.0,
                    valuation_score=90.0, momentum_score=60.0,
                    liquidity_score=80.0, fund_score=50.0, rank=1
                )
            ],
            winner="000001",
        )

        assert result.date == "2026-03-08"
        assert len(result.stocks) == 1
        assert result.winner == "000001"

    def test_to_dict(self):
        """测试转换为字典"""
        result = CompareResult(
            date="2026-03-08",
            stocks=[],
            scores=[],
            winner=None,
        )

        data = result.to_dict()

        assert data["date"] == "2026-03-08"
        assert "stocks" in data
        assert "scores" in data


class TestFormatCompareResult:
    """格式化对比结果测试"""

    def test_format_result(self):
        """测试格式化结果"""
        result = CompareResult(
            date="2026-03-08",
            stocks=[
                StockMetrics(
                    code="000001", name="平安银行", price=12.50,
                    change_pct=2.0, turnover_rate=5.0, amount=10.0,
                    market_cap=2400.0
                )
            ],
            scores=[
                StockScore(
                    code="000001", name="平安银行", total_score=75.0,
                    valuation_score=90.0, momentum_score=60.0,
                    liquidity_score=80.0, fund_score=50.0, rank=1
                )
            ],
            winner="000001",
        )

        text = format_compare_result(result)

        assert "2026-03-08" in text
        assert "000001" in text
        assert "平安银行" in text
        assert "综合评分最高" in text
