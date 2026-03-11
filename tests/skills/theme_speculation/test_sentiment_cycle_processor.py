# -*- coding: utf-8 -*-
"""情绪周期 Processor 测试"""

import pytest
from unittest.mock import AsyncMock, patch

from openclaw_alpha.skills.theme_speculation.sentiment_cycle_processor.sentiment_cycle_processor import (
    SentimentCycleProcessor,
    SentimentIndicators,
)
from openclaw_alpha.skills.limit_up_tracker.limit_up_fetcher.models import (
    LimitUpItem,
    LimitUpType,
    LimitUpResult,
)


def create_limit_up_item(
    code: str,
    name: str,
    continuous: int = 3,
    first_limit_time: str = "09:35:00",
    change_pct: float = 10.0,
) -> LimitUpItem:
    """创建涨停股数据（测试辅助函数）"""
    return LimitUpItem(
        code=code,
        name=name,
        continuous=continuous,
        first_limit_time=first_limit_time,
        last_limit_time=first_limit_time,
        float_mv=100.0,
        total_mv=200.0,
        change_pct=change_pct,
        price=12.0,
        amount=10.0,
        turnover_rate=5.0,
        limit_times=0,
        limit_stat=f"{continuous}/{continuous}",
        industry="测试行业",
    )


class TestSentimentIndicators:
    """测试情绪指标数据类"""

    def test_to_dict(self):
        """测试转换为字典"""
        indicators = SentimentIndicators(
            limit_up_count=50,
            broken_count=10,
            broken_rate=16.67,
            max_continuous=3,
            prev_avg_change=2.5,
            prev_profit_rate=60.0,
        )

        result = indicators.to_dict()

        assert result["limit_up_count"] == 50
        assert result["broken_count"] == 10
        assert result["broken_rate"] == 16.67
        assert result["max_continuous"] == 3
        assert result["prev_avg_change"] == 2.5
        assert result["prev_profit_rate"] == 60.0


class TestSentimentCycleProcessor:
    """测试情绪周期处理器"""

    @pytest.fixture
    def processor(self):
        """创建处理器实例"""
        return SentimentCycleProcessor("2026-03-11")

    def test_determine_cycle_retreat(self, processor):
        """测试退潮周期：涨停家数 < 30 且 昨日涨停盈利比例 < 40%"""
        processor.indicators = SentimentIndicators(
            limit_up_count=25,
            broken_count=5,
            broken_rate=16.67,
            max_continuous=2,
            prev_avg_change=-2.0,
            prev_profit_rate=35.0,
        )

        cycle, reasons = processor._determine_cycle()

        assert cycle == "退潮"
        assert len(reasons) == 2
        assert "涨停家数锐减" in reasons[0]
        assert "昨日涨停亏损率高" in reasons[1]

    def test_determine_cycle_divergence(self, processor):
        """测试分歧周期：炸板率 > 50%"""
        processor.indicators = SentimentIndicators(
            limit_up_count=60,
            broken_count=70,
            broken_rate=53.85,
            max_continuous=3,
            prev_avg_change=0.5,
            prev_profit_rate=50.0,
        )

        cycle, reasons = processor._determine_cycle()

        assert cycle == "分歧"
        assert any("炸板率高" in r for r in reasons)

    def test_determine_cycle_climax(self, processor):
        """测试高潮周期：涨停家数 > 100 且 最高连板数 >= 5 且 盈利比例 > 40%"""
        processor.indicators = SentimentIndicators(
            limit_up_count=120,
            broken_count=30,
            broken_rate=20.0,
            max_continuous=6,
            prev_avg_change=3.0,
            prev_profit_rate=70.0,
        )

        cycle, reasons = processor._determine_cycle()

        assert cycle == "高潮"
        assert any("涨停家数达到峰值" in r for r in reasons)
        assert any("最高连板数" in r for r in reasons)

    def test_determine_cycle_climax_with_low_profit(self, processor):
        """测试高潮周期（盈利比例低）：涨停家数 > 100 但 盈利比例 < 40% → 不是高潮"""
        processor.indicators = SentimentIndicators(
            limit_up_count=120,
            broken_count=30,
            broken_rate=20.0,
            max_continuous=6,
            prev_avg_change=-2.0,
            prev_profit_rate=30.0,
        )

        cycle, reasons = processor._determine_cycle()

        # 应该判断为"分歧"而不是"高潮"
        assert cycle == "分歧"
        assert any("昨日涨停表现分化" in r for r in reasons)

    def test_determine_cycle_acceleration(self, processor):
        """测试加速周期：涨停家数 > 50 且 最高连板数 >= 3 且 盈利比例 > 40%"""
        processor.indicators = SentimentIndicators(
            limit_up_count=65,
            broken_count=10,
            broken_rate=13.33,
            max_continuous=4,
            prev_avg_change=2.0,
            prev_profit_rate=65.0,
        )

        cycle, reasons = processor._determine_cycle()

        assert cycle == "加速"
        assert any("涨停家数增加" in r for r in reasons)

    def test_determine_cycle_acceleration_with_low_profit(self, processor):
        """测试加速周期（盈利比例低）：涨停家数 > 50 但 盈利比例 < 40% → 分歧"""
        processor.indicators = SentimentIndicators(
            limit_up_count=74,
            broken_count=19,
            broken_rate=20.43,
            max_continuous=7,
            prev_avg_change=-3.71,
            prev_profit_rate=26.83,
        )

        cycle, reasons = processor._determine_cycle()

        # 应该判断为"分歧"而不是"加速"
        assert cycle == "分歧"
        assert any("昨日涨停表现分化" in r for r in reasons)

    def test_determine_cycle_startup(self, processor):
        """测试启动周期：涨停家数 > 20 且 炸板率 < 30% 且 昨日涨停平均涨跌 > 0"""
        processor.indicators = SentimentIndicators(
            limit_up_count=35,
            broken_count=5,
            broken_rate=12.5,
            max_continuous=2,
            prev_avg_change=1.5,
            prev_profit_rate=60.0,
        )

        cycle, reasons = processor._determine_cycle()

        assert cycle == "启动"
        assert any("涨停家数增加" in r for r in reasons)
        assert any("炸板率低" in r for r in reasons)
        assert any("昨日涨停正收益" in r for r in reasons)

    def test_determine_cycle_default(self, processor):
        """测试默认情况：无明确信号"""
        processor.indicators = SentimentIndicators(
            limit_up_count=10,
            broken_count=5,
            broken_rate=33.33,
            max_continuous=1,
            prev_avg_change=-1.0,
            prev_profit_rate=40.0,
        )

        cycle, reasons = processor._determine_cycle()

        assert cycle == "启动"
        assert any("暂无明显信号" in r for r in reasons)

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    @patch("openclaw_alpha.skills.theme_speculation.sentiment_cycle_processor.sentiment_cycle_processor.fetch_limit_up")
    async def test_analyze(self, mock_fetch, processor):
        """测试完整分析流程"""
        # Mock 涨停数据
        limit_up_result = LimitUpResult(
            date="2026-03-11",
            limit_type=LimitUpType.LIMIT_UP,
            total=50,
            continuous_stat={},
            items=[create_limit_up_item("000001", "平安银行", continuous=3)],
        )

        # Mock 炸板数据
        broken_result = LimitUpResult(
            date="2026-03-11",
            limit_type=LimitUpType.BROKEN,
            total=10,
            continuous_stat={},
            items=[],
        )

        # Mock 昨日涨停表现
        prev_result = LimitUpResult(
            date="2026-03-10",
            limit_type=LimitUpType.PREVIOUS,
            total=20,
            continuous_stat={},
            items=[create_limit_up_item("000002", "万科A", continuous=1, change_pct=2.5)],
        )

        mock_fetch.side_effect = [
            limit_up_result,  # 第一次调用：今日涨停
            broken_result,    # 第二次调用：炸板
            prev_result,      # 第三次调用：昨日涨停表现
        ]

        result = await processor.analyze()

        assert result.date == "2026-03-11"
        assert result.cycle in ["启动", "加速", "高潮", "分歧", "退潮"]
        assert result.indicators.limit_up_count == 50
        assert len(result.reasons) > 0
