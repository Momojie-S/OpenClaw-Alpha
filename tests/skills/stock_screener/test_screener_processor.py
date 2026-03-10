# -*- coding: utf-8 -*-
"""ScreenerProcessor 测试"""

import pytest

from openclaw_alpha.skills.stock_screener.stock_spot_fetcher.stock_spot_fetcher import StockSpot
from openclaw_alpha.skills.stock_screener.screener_processor.screener_processor import (
    FilterConditions,
    ScreenerProcessor,
    STRATEGIES,
)


# 测试数据（市值单位：亿元）
def create_spots() -> list[StockSpot]:
    """创建测试股票数据"""
    return [
        StockSpot("000001", "平安银行", 2.35, 1.25, 15.0, 12.5, 2500.0),    # 2500亿
        StockSpot("000002", "万科A", -1.5, 0.85, 8.0, 8.2, 1800.0),        # 1800亿
        StockSpot("300001", "特锐德", 5.8, 8.5, 25.0, 25.6, 800.0),        # 800亿
        StockSpot("300002", "神州泰岳", 10.02, 12.3, 35.0, 6.8, 350.0),    # 350亿
        StockSpot("600000", "浦发银行", 0.5, 0.3, 5.0, 9.5, 2800.0),       # 2800亿
        StockSpot("600519", "贵州茅台", 1.2, 0.15, 50.0, 1850.0, 23200.0), # 23200亿
        StockSpot("601318", "中国平安", -0.8, 0.25, 12.0, 45.5, 8200.0),   # 8200亿
        StockSpot("002475", "立讯精密", 3.5, 2.1, 18.0, 32.8, 4500.0),     # 4500亿
        StockSpot("002594", "比亚迪", 4.2, 1.8, 85.0, 285.0, 8500.0),      # 8500亿
        StockSpot("000651", "格力电器", 0.0, 0.45, 6.0, 38.5, 2200.0),     # 2200亿
    ]


class TestFilterConditions:
    """测试筛选条件"""

    def test_from_strategy_valid(self):
        """测试从有效策略创建条件"""
        conditions = FilterConditions.from_strategy("volume_breakout")
        assert conditions is not None
        assert conditions.change_min == 3.0
        assert conditions.turnover_min == 5.0
        assert conditions.amount_min == 2.0

    def test_from_strategy_invalid(self):
        """测试从无效策略创建条件"""
        conditions = FilterConditions.from_strategy("invalid_strategy")
        assert conditions is None

    def test_to_dict(self):
        """测试转换为字典"""
        conditions = FilterConditions(change_min=3.0, turnover_max=5.0)
        result = conditions.to_dict()
        assert result == {"change_min": 3.0, "turnover_max": 5.0}


class TestScreenerProcessor:
    """测试选股筛选器"""

    @pytest.fixture
    def processor(self):
        return ScreenerProcessor()

    @pytest.fixture
    def spots(self):
        return create_spots()

    def test_filter_change_min(self, processor, spots):
        """测试涨幅筛选"""
        conditions = FilterConditions(change_min=3.0)
        result = processor.filter(spots, conditions)

        # 应该有 4 只股票涨幅 >= 3%
        assert len(result) == 4
        assert all(s.change_pct >= 3.0 for s in result)

    def test_filter_change_range(self, processor, spots):
        """测试涨幅区间筛选"""
        conditions = FilterConditions(change_min=0.0, change_max=5.0)
        result = processor.filter(spots, conditions)

        # 涨幅 0~5% 的股票：平安银行、浦发银行、茅台、立讯精密、比亚迪、格力
        assert len(result) == 6
        assert all(0.0 <= s.change_pct <= 5.0 for s in result)

    def test_filter_turnover(self, processor, spots):
        """测试换手率筛选"""
        conditions = FilterConditions(turnover_min=5.0)
        result = processor.filter(spots, conditions)

        # 换手率 >= 5% 的股票
        assert len(result) == 2
        assert all(s.turnover_rate >= 5.0 for s in result)

    def test_filter_amount(self, processor, spots):
        """测试成交额筛选"""
        conditions = FilterConditions(amount_min=10.0)
        result = processor.filter(spots, conditions)

        # 成交额 >= 10 亿的股票
        assert len(result) == 7
        assert all(s.amount >= 10.0 for s in result)

    def test_filter_market_cap(self, processor, spots):
        """测试市值筛选"""
        conditions = FilterConditions(cap_min=5000.0)  # 市值 >= 5000 亿
        result = processor.filter(spots, conditions)

        # 市值 >= 5000亿：茅台(23200)、平安(8200)、比亚迪(8500)
        assert len(result) == 3

    def test_filter_combined(self, processor, spots):
        """测试组合条件筛选"""
        # 放量突破：涨幅 > 3%，换手率 > 5%，成交额 > 2 亿
        conditions = FilterConditions(
            change_min=3.0,
            turnover_min=5.0,
            amount_min=2.0,
        )
        result = processor.filter(spots, conditions)

        # 特锐德和神州泰岳符合
        assert len(result) == 2
        assert all(s.change_pct >= 3.0 and s.turnover_rate >= 5.0 for s in result)

    def test_filter_no_match(self, processor, spots):
        """测试无匹配结果"""
        conditions = FilterConditions(change_min=20.0)
        result = processor.filter(spots, conditions)

        assert len(result) == 0

    def test_sort_by_change_desc(self, processor, spots):
        """测试按涨幅降序排序"""
        result = processor.sort_by_change(spots, descending=True)

        assert result[0].change_pct == 10.02  # 神州泰岳
        assert result[-1].change_pct == -1.5  # 万科A

    def test_sort_by_change_asc(self, processor, spots):
        """测试按涨幅升序排序"""
        result = processor.sort_by_change(spots, descending=False)

        assert result[0].change_pct == -1.5  # 万科A
        assert result[-1].change_pct == 10.02  # 神州泰岳

    def test_to_screen_results(self, processor, spots):
        """测试转换输出格式"""
        top_3 = spots[:3]
        result = processor.to_screen_results(top_3)

        assert len(result) == 3
        assert result[0].code == "000001"
        assert result[0].name == "平安银行"
        assert result[0].change_pct == 2.35


class TestStrategies:
    """测试预设策略"""

    def test_volume_breakout_strategy(self):
        """测试放量突破策略"""
        conditions = FilterConditions.from_strategy("volume_breakout")
        processor = ScreenerProcessor()
        spots = create_spots()

        result = processor.filter(spots, conditions)
        # 特锐德 (5.8%, 8.5%) 和 神州泰岳 (10.02%, 12.3%)
        assert len(result) == 2

    def test_leader_strategy(self):
        """测试龙头股策略"""
        conditions = FilterConditions.from_strategy("leader")
        processor = ScreenerProcessor()
        spots = create_spots()

        result = processor.filter(spots, conditions)
        # 涨幅 > 5%，成交额 > 10 亿，市值 > 100 亿
        # 特锐德 (5.8%, 25亿, 800亿) 和 神州泰岳 (10.02%, 35亿, 350亿) 符合
        assert len(result) == 2

    def test_small_active_strategy(self):
        """测试小盘活跃策略"""
        conditions = FilterConditions.from_strategy("small_active")
        processor = ScreenerProcessor()
        spots = create_spots()

        result = processor.filter(spots, conditions)
        # 换手率 >= 8%，市值 < 50 亿（cap_max=50）
        # 特锐德 (8.5%, 800亿), 神州泰岳 (12.3%, 350亿)
        # 市值都不 < 50 亿，所以无匹配
        assert len(result) == 0

    def test_blue_chip_strategy(self):
        """测试蓝筹股策略"""
        conditions = FilterConditions.from_strategy("blue_chip")
        processor = ScreenerProcessor()
        spots = create_spots()

        result = processor.filter(spots, conditions)
        # 市值 >= 500 亿（cap_min=500），换手率 <= 2%
        # 符合条件的有：平安银行、万科A、浦发、茅台、平安、比亚迪、格力
        assert len(result) == 7
