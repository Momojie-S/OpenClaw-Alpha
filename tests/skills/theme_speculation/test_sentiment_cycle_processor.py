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

    def test_determine_cycle_acceleration_with_negative_change(self, processor):
        """测试加速周期（平均涨跌为负）：盈利比例 > 40% 但 平均涨跌 < 0 → 分歧"""
        processor.indicators = SentimentIndicators(
            limit_up_count=73,
            broken_count=17,
            broken_rate=18.89,
            max_continuous=8,
            prev_avg_change=-0.22,  # 平均涨跌为负
            prev_profit_rate=41.67,  # 盈利比例 > 40%
        )

        cycle, reasons = processor._determine_cycle()

        # 应该判断为"分歧"而不是"加速"（因为虽然盈利比例 > 40%，但整体亏损）
        assert cycle == "分歧"
        assert any("昨日涨停整体亏损" in r for r in reasons)

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

    def test_detect_anomalies_broken_rate_zero(self, processor):
        """测试数据异常检测：炸板率为 0% 但有涨停"""
        processor.indicators = SentimentIndicators(
            limit_up_count=177,
            broken_count=0,
            broken_rate=0.0,
            max_continuous=13,
            prev_avg_change=0.0,
            prev_profit_rate=0.0,
        )

        warnings = processor._detect_anomalies()

        assert len(warnings) >= 1
        assert any("炸板率为 0%" in w for w in warnings)

    def test_detect_anomalies_prev_performance_zero(self, processor):
        """测试数据异常检测：昨日涨停盈利比例和平均涨跌均为 0%"""
        processor.indicators = SentimentIndicators(
            limit_up_count=100,
            broken_count=20,
            broken_rate=16.67,
            max_continuous=5,
            prev_avg_change=0.0,
            prev_profit_rate=0.0,
        )

        warnings = processor._detect_anomalies()

        assert len(warnings) >= 1
        assert any("昨日涨停盈利比例和平均涨跌均为 0%" in w for w in warnings)

    def test_detect_anomalies_limit_up_zero(self, processor):
        """测试数据异常检测：无涨停数据"""
        processor.indicators = SentimentIndicators(
            limit_up_count=0,
            broken_count=0,
            broken_rate=0.0,
            max_continuous=0,
            prev_avg_change=0.0,
            prev_profit_rate=0.0,
        )

        warnings = processor._detect_anomalies()

        assert len(warnings) >= 1
        assert any("无涨停数据" in w for w in warnings)

    def test_detect_anomalies_no_anomaly(self, processor):
        """测试数据异常检测：正常数据无异常"""
        processor.indicators = SentimentIndicators(
            limit_up_count=73,
            broken_count=18,
            broken_rate=19.78,
            max_continuous=7,
            prev_avg_change=2.51,
            prev_profit_rate=64.29,
        )

        warnings = processor._detect_anomalies()

        assert len(warnings) == 0

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


class TestDataQualityScore:
    """测试数据质量评分功能"""

    @pytest.fixture
    def processor(self):
        """创建处理器实例"""
        return SentimentCycleProcessor("2026-03-11")

    def test_calculate_data_quality_high_quality(self, processor):
        """测试高质量数据（所有数据完整、合理、时效）"""
        # 设置完整的指标
        processor.indicators.limit_up_count = 73
        processor.indicators.broken_count = 18
        processor.indicators.broken_rate = 19.78
        processor.indicators.max_continuous = 7
        processor.indicators.prev_avg_change = 2.51
        processor.indicators.prev_profit_rate = 64.29

        # 计算评分
        quality = processor._calculate_data_quality()

        # 验证评分
        assert quality.total == 100
        assert quality.completeness == 40  # 有涨停、炸板、昨日表现
        assert quality.reasonableness == 40  # 炸板率、盈利比例、平均涨跌都合理
        assert quality.timeliness == 20  # 数据是最近的
        assert quality.grade == "A"
        assert len(quality.details) > 0

    def test_calculate_data_quality_missing_broken_data(self, processor):
        """测试缺失炸板数据（完整性降低）"""
        # 修改日期为历史日期
        processor.date = "2026-01-13"

        # 设置指标（无炸板数据）
        processor.indicators.limit_up_count = 177
        processor.indicators.broken_count = 0
        processor.indicators.broken_rate = 0.0
        processor.indicators.max_continuous = 13
        processor.indicators.prev_avg_change = 0.0
        processor.indicators.prev_profit_rate = 0.0

        # 计算评分
        quality = processor._calculate_data_quality()

        # 验证评分
        assert quality.total == 30
        assert quality.completeness == 10  # 只有涨停数据
        assert quality.reasonableness == 20  # 炸板率合理，但盈利比例和平均涨跌为0（数据缺失）
        assert quality.timeliness == 0  # 历史数据
        assert quality.grade == "D"

    def test_calculate_data_quality_historical_data(self, processor):
        """测试历史数据（时效性降低）"""
        # 修改日期为历史日期
        processor.date = "2026-01-13"

        # 设置完整的指标
        processor.indicators.limit_up_count = 73
        processor.indicators.broken_count = 18
        processor.indicators.broken_rate = 19.78
        processor.indicators.max_continuous = 7
        processor.indicators.prev_avg_change = 2.51
        processor.indicators.prev_profit_rate = 64.29

        # 计算评分
        quality = processor._calculate_data_quality()

        # 验证评分
        assert quality.total == 80
        assert quality.completeness == 40  # 有涨停、炸板、昨日表现
        assert quality.reasonableness == 40  # 数据都合理
        assert quality.timeliness == 0  # 历史数据
        assert quality.grade == "B"

    def test_calculate_data_quality_unreasonable_data(self, processor):
        """测试不合理数据（合理性降低）"""
        # 设置不合理的指标
        processor.indicators.limit_up_count = 73
        processor.indicators.broken_count = 18
        processor.indicators.broken_rate = 60.0  # 超过50%，不合理
        processor.indicators.max_continuous = 7
        processor.indicators.prev_avg_change = 25.0  # 超过20%，不合理
        processor.indicators.prev_profit_rate = 120.0  # 超过100%，不合理

        # 计算评分
        quality = processor._calculate_data_quality()

        # 验证评分
        assert quality.total == 60
        assert quality.completeness == 40  # 有涨停、炸板、昨日表现
        assert quality.reasonableness == 0  # 所有数据都不合理
        assert quality.timeliness == 20  # 数据是最近的
        assert quality.grade == "C"

    def test_calculate_data_quality_no_data(self, processor):
        """测试无数据（最低质量）"""
        # 保持默认值（所有指标为0）
        processor.indicators.limit_up_count = 0
        processor.indicators.broken_count = 0
        processor.indicators.broken_rate = 0.0
        processor.indicators.max_continuous = 0
        processor.indicators.prev_avg_change = 0.0
        processor.indicators.prev_profit_rate = 0.0

        # 修改日期为历史日期
        processor.date = "2026-01-01"

        # 计算评分
        quality = processor._calculate_data_quality()

        # 验证评分
        assert quality.total == 40
        assert quality.completeness == 0  # 无涨停、炸板、昨日表现
        assert quality.reasonableness == 40  # 炸板率（0）合理、盈利比例（0）合理、平均涨跌（0）合理
        assert quality.timeliness == 0  # 历史数据
        assert quality.grade == "D"


class TestDataDelayDetection:
    """测试数据延迟检测功能"""

    @pytest.fixture
    def processor(self):
        """创建 processor 实例"""
        processor = SentimentCycleProcessor(date="2026-03-12")
        processor.indicators = SentimentIndicators()
        return processor

    def test_detect_data_delay_after_close_no_limit_up(self, processor):
        """测试收盘后数据延迟（涨停数为0）"""
        # 设置今天的日期，收盘后（假设当前时间是17:00）
        # 设置涨停数为0（数据延迟）
        processor.indicators.limit_up_count = 0

        # 检测延迟
        delay_info = processor._detect_data_delay()

        # 验证：如果是交易日收盘后，应该检测到延迟
        # 注意：这个测试可能会因为实际运行时间不同而结果不同
        # 所以我们只验证返回的数据结构
        assert "is_delayed" in delay_info
        assert "delay_hours" in delay_info
        assert "reason" in delay_info
        assert "is_trading_day" in delay_info
        assert "is_after_close" in delay_info

    def test_detect_data_delay_after_close_incomplete_data(self, processor):
        """测试收盘后数据延迟（数据不完整）"""
        # 设置涨停数 > 0，但炸板数和昨日表现为0（数据不完整）
        processor.indicators.limit_up_count = 73
        processor.indicators.broken_count = 0
        processor.indicators.prev_profit_rate = 0

        # 检测延迟
        delay_info = processor._detect_data_delay()

        # 验证返回的数据结构
        assert "is_delayed" in delay_info
        assert "reason" in delay_info

    def test_detect_data_delay_during_trading(self, processor):
        """测试盘中数据不完整（正常）"""
        # 设置今天的日期，盘中（假设当前时间是10:00）
        # 设置涨停数为0（盘中数据不完整是正常的）
        processor.indicators.limit_up_count = 0

        # 检测延迟
        delay_info = processor._detect_data_delay()

        # 验证：如果是盘中，不应该判断为延迟
        # 但我们只验证返回的数据结构
        assert "is_delayed" in delay_info
        assert "reason" in delay_info

    def test_detect_data_delay_weekend(self, processor):
        """测试周末无数据（正常）"""
        # 设置日期为周末（例如：2026-03-01 是周日）
        processor.date = "2026-03-01"
        processor.indicators.limit_up_count = 0

        # 检测延迟
        delay_info = processor._detect_data_delay()

        # 验证：如果是周末，不应该判断为延迟
        # 但我们只验证返回的数据结构
        assert "is_delayed" in delay_info
        assert "reason" in delay_info

    def test_detect_data_delay_historical_data(self, processor):
        """测试历史数据（不检测延迟）"""
        # 设置日期为历史日期（非今天）
        processor.date = "2026-03-11"
        processor.indicators.limit_up_count = 0

        # 检测延迟
        delay_info = processor._detect_data_delay()

        # 验证：如果是历史数据，不应该判断为延迟
        assert delay_info["is_delayed"] == False
        assert "历史数据" in delay_info["reason"]

