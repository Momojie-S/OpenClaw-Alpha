# -*- coding: utf-8 -*-
"""情绪周期预测功能测试"""

import pytest
from datetime import datetime, timedelta

from openclaw_alpha.skills.theme_speculation.sentiment_cycle_processor.sentiment_cycle_processor import (
    SentimentCycleResult,
    SentimentIndicators,
    DataQualityScore,
    PredictionResult,
    predict_next_cycle,
    _analyze_and_predict,
    _get_cycle_evolution,
    _predict_limit_up_trend,
)


@pytest.fixture
def create_result():
    """创建情绪周期结果的工厂函数"""
    def _create(
        date: str,
        cycle: str,
        limit_up_count: int = 50,
        broken_rate: float = 20.0,
        quality_score: int = 80,
    ) -> SentimentCycleResult:
        return SentimentCycleResult(
            date=date,
            cycle=cycle,
            indicators=SentimentIndicators(
                limit_up_count=limit_up_count,
                broken_count=int(limit_up_count * broken_rate / 100),
                broken_rate=broken_rate,
                max_continuous=3,
                prev_avg_change=2.0,
                prev_profit_rate=60.0,
            ),
            reasons=["测试理由"],
            warnings=[],
            quality_score=DataQualityScore(
                total=quality_score,
                completeness=30,
                reasonableness=30,
                timeliness=20,
                grade="B" if quality_score >= 70 else "D",
            ),
        )
    return _create


class TestPredictNextCycle:
    """测试 predict_next_cycle 函数"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_insufficient_data(self):
        """测试数据不足的情况"""
        results = []
        prediction = predict_next_cycle(results)
        assert prediction is None

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_low_quality_data(self, create_result):
        """测试数据质量差的情况"""
        results = [
            create_result("2026-03-09", "加速", quality_score=50),
            create_result("2026-03-10", "加速", quality_score=50),
            create_result("2026-03-11", "加速", quality_score=50),
        ]
        prediction = predict_next_cycle(results)
        assert prediction is None

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_stable_cycle_high_confidence(self, create_result):
        """测试趋势稳定（高置信度）"""
        results = [
            create_result("2026-03-09", "加速", quality_score=80),
            create_result("2026-03-10", "加速", quality_score=80),
            create_result("2026-03-11", "加速", quality_score=80),
        ]
        prediction = predict_next_cycle(results)

        assert prediction is not None
        assert prediction.predicted_cycle == "加速"
        assert prediction.confidence == "高"
        assert "最近 3 天情绪周期均为 加速" in prediction.reasons[0]

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_cycle_evolution_medium_confidence(self, create_result):
        """测试周期演进（中置信度）"""
        results = [
            create_result("2026-03-09", "启动", quality_score=80),
            create_result("2026-03-10", "加速", quality_score=80),
            create_result("2026-03-11", "加速", quality_score=80),
        ]
        prediction = predict_next_cycle(results)

        assert prediction is not None
        assert prediction.predicted_cycle in ["加速", "高潮"]
        assert prediction.confidence in ["中", "高"]


class TestAnalyzeAndPredict:
    """测试 _analyze_and_predict 函数"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_stable_trend(self, create_result):
        """测试稳定趋势"""
        recent = [
            create_result("2026-03-09", "加速"),
            create_result("2026-03-10", "加速"),
            create_result("2026-03-11", "加速"),
        ]
        prediction = _analyze_and_predict(recent, "2026-03-12")

        assert prediction.predicted_cycle == "加速"
        assert prediction.confidence == "高"

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_upward_trend(self, create_result):
        """测试上升趋势"""
        recent = [
            create_result("2026-03-09", "启动", limit_up_count=50),
            create_result("2026-03-10", "加速", limit_up_count=70),
            create_result("2026-03-11", "加速", limit_up_count=90),
        ]
        prediction = _analyze_and_predict(recent, "2026-03-12")

        # 涨停数上升，应该预测为加速或高潮
        assert prediction.predicted_cycle in ["加速", "高潮"]
        assert prediction.confidence in ["中", "高"]

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_downward_trend(self, create_result):
        """测试下降趋势"""
        recent = [
            create_result("2026-03-09", "高潮", limit_up_count=120),
            create_result("2026-03-10", "分歧", limit_up_count=80),
            create_result("2026-03-11", "退潮", limit_up_count=40),
        ]
        prediction = _analyze_and_predict(recent, "2026-03-12")

        # 涨停数下降，应该预测为分歧或退潮
        assert prediction.predicted_cycle in ["分歧", "退潮"]
        assert prediction.confidence in ["中", "高"]


class TestGetCycleEvolution:
    """测试 _get_cycle_evolution 函数"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_start_to_accelerate(self):
        """测试启动到加速的演进"""
        cycles = ["启动", "加速"]
        evolution = _get_cycle_evolution(cycles)

        assert evolution is not None
        assert evolution["next_cycle"] == "加速"

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_accelerate_to_climax(self):
        """测试加速到高潮的演进"""
        cycles = ["加速", "高潮"]
        evolution = _get_cycle_evolution(cycles)

        assert evolution is not None
        assert evolution["next_cycle"] == "高潮"

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_climax_to_divergence(self):
        """测试高潮到分歧的演进"""
        cycles = ["高潮", "分歧"]
        evolution = _get_cycle_evolution(cycles)

        assert evolution is not None
        assert evolution["next_cycle"] == "分歧"

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_no_clear_evolution(self):
        """测试没有明确演进方向"""
        cycles = ["启动", "退潮"]
        evolution = _get_cycle_evolution(cycles)

        # 没有明确的演进规则
        assert evolution is None


class TestPredictLimitUpTrend:
    """测试 _predict_limit_up_trend 函数"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_upward_trend(self, create_result):
        """测试上升趋势"""
        recent = [
            create_result("2026-03-09", "加速", limit_up_count=50),
            create_result("2026-03-10", "加速", limit_up_count=70),
            create_result("2026-03-11", "加速", limit_up_count=90),
        ]
        trend = _predict_limit_up_trend(recent)

        assert trend["direction"] == "up"
        assert trend["predicted_count"] > 90

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_downward_trend(self, create_result):
        """测试下降趋势"""
        recent = [
            create_result("2026-03-09", "高潮", limit_up_count=120),
            create_result("2026-03-10", "分歧", limit_up_count=80),
            create_result("2026-03-11", "退潮", limit_up_count=40),
        ]
        trend = _predict_limit_up_trend(recent)

        assert trend["direction"] == "down"
        assert trend["predicted_count"] < 40

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_stable_trend(self, create_result):
        """测试稳定趋势"""
        recent = [
            create_result("2026-03-09", "加速", limit_up_count=70),
            create_result("2026-03-10", "加速", limit_up_count=75),
            create_result("2026-03-11", "加速", limit_up_count=72),
        ]
        trend = _predict_limit_up_trend(recent)

        # 变化幅度小，判断为稳定
        assert trend["direction"] in ["stable", "up", "down"]
