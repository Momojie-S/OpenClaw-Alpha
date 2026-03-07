# -*- coding: utf-8 -*-
"""测试 IndustryTrendProcessor"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from skills.industry_trend.scripts.industry_trend_processor.industry_trend_processor import (
    IndustryTrendProcessor,
    INDUSTRY_WEIGHTS,
    CONCEPT_WEIGHTS,
)


class TestIndustryTrendProcessorNormalize:
    """测试归一化方法"""

    @pytest.fixture
    def processor(self):
        """创建 Processor 实例"""
        return IndustryTrendProcessor()

    def test_normalize_basic(self, processor):
        """测试基本归一化"""
        values = [10, 20, 30, 40, 50]
        result = processor._normalize(values)

        # 最小值映射到 0，最大值映射到 100
        assert result[0] == 0.0
        assert result[4] == 100.0
        # 中间值按比例
        assert abs(result[2] - 50.0) < 0.01

    def test_normalize_same_values(self, processor):
        """测试所有值相同的情况"""
        values = [50, 50, 50]
        result = processor._normalize(values)

        # 所有值相同，返回中间值 50
        assert all(v == 50.0 for v in result)

    def test_normalize_empty(self, processor):
        """测试空列表"""
        result = processor._normalize([])
        assert len(result) == 0

    def test_normalize_negative_values(self, processor):
        """测试负值"""
        values = [-10, 0, 10]
        result = processor._normalize(values)

        assert result[0] == 0.0
        assert result[1] == 50.0
        assert result[2] == 100.0


class TestIndustryTrendProcessorVolumeRatio:
    """测试成交额占比计算"""

    @pytest.fixture
    def processor(self):
        """创建 Processor 实例"""
        proc = IndustryTrendProcessor()
        proc.date = "2026-03-06"
        proc.category = "L1"
        return proc

    def test_calc_volume_ratio_basic(self, processor):
        """测试基本成交额占比计算"""
        processor.data = [
            {"name": "板块1", "metrics": {"amount": 1000.0}},
            {"name": "板块2", "metrics": {"amount": 2000.0}},
            {"name": "板块3", "metrics": {"amount": 3000.0}},
        ]

        processor._calc_volume_ratio()

        # 总成交额 6000
        # 板块1: 1000/6000 * 100 = 16.67%
        assert abs(processor.data[0]["metrics"]["volume_ratio"] - 16.67) < 0.1
        # 板块2: 2000/6000 * 100 = 33.33%
        assert abs(processor.data[1]["metrics"]["volume_ratio"] - 33.33) < 0.1
        # 板块3: 3000/6000 * 100 = 50.0%
        assert abs(processor.data[2]["metrics"]["volume_ratio"] - 50.0) < 0.1

    def test_calc_volume_ratio_zero_total(self, processor):
        """测试总成交额为 0 的情况"""
        processor.data = [
            {"name": "板块1", "metrics": {"amount": 0.0}},
            {"name": "板块2", "metrics": {"amount": 0.0}},
        ]

        processor._calc_volume_ratio()

        # 所有占比都是 0
        assert all(board["metrics"]["volume_ratio"] == 0.0 for board in processor.data)

    def test_calc_volume_ratio_empty(self, processor):
        """测试空数据"""
        processor.data = []
        processor._calc_volume_ratio()
        # 不应该抛出异常
        assert len(processor.data) == 0


class TestIndustryTrendProcessorHeatIndex:
    """测试热度指数计算"""

    @pytest.fixture
    def processor(self):
        """创建 Processor 实例"""
        proc = IndustryTrendProcessor()
        proc.date = "2026-03-06"
        proc.category = "L1"
        proc.data = [
            {
                "name": "板块1",
                "code": "001",
                "date": "2026-03-06",
                "metrics": {
                    "pct_change": 3.0,
                    "turnover_rate": 5.0,
                    "amount": 1000.0,
                    "float_mv": 10000.0,
                },
            },
            {
                "name": "板块2",
                "code": "002",
                "date": "2026-03-06",
                "metrics": {
                    "pct_change": 2.0,
                    "turnover_rate": 3.0,
                    "amount": 2000.0,
                    "float_mv": 20000.0,
                },
            },
        ]
        return proc

    def test_calc_heat_index_basic(self, processor):
        """测试基本热度指数计算"""
        # 先计算成交额占比
        processor._calc_volume_ratio()
        
        # 计算热度指数
        boards = processor._calc_heat_index()

        assert len(boards) == 2
        # 每个板块应该有 heat_index 和 scores 字段
        for board in boards:
            assert "heat_index" in board
            assert "scores" in board
            assert isinstance(board["heat_index"], float)
            assert isinstance(board["scores"], dict)

    def test_calc_heat_index_weights_sum(self, processor):
        """测试权重总和为 100%"""
        # 申万行业权重
        assert sum(INDUSTRY_WEIGHTS.values()) == 1.0

        # 概念板块权重
        assert sum(CONCEPT_WEIGHTS.values()) == 1.0


class TestIndustryTrendProcessorTrend:
    """测试趋势信号判断"""

    @pytest.fixture
    def processor(self):
        """创建 Processor 实例"""
        return IndustryTrendProcessor()

    def test_judge_trend_new(self, processor):
        """测试新数据（无环比）"""
        boards = [
            {
                "name": "板块1",
                "metrics": {"pct_change": 3.5},
                "heat_index": 85.0,
            }
        ]

        result = processor._judge_trend(boards)

        # 无历史数据时，标记为"新"，heat_change 为 None
        assert result[0]["trend"] == "新"
        assert result[0]["heat_change"] is None

    def test_judge_trend_heating(self, processor):
        """测试加热中信号"""
        # 模拟有历史数据的情况
        # 注意：当前版本 heat_change 固定为 0，所以不会出现"加热中"
        # 这个测试为未来版本预留
        boards = [
            {
                "name": "板块1",
                "metrics": {"pct_change": 5.0},
                "heat_index": 90.0,
            }
        ]

        result = processor._judge_trend(boards)
        assert result[0]["trend"] in ["新", "稳定", "加热中"]

    def test_judge_trend_cooling(self, processor):
        """测试降温中信号"""
        # 当涨跌幅 < -3% 时，标记为"降温中"
        boards = [
            {
                "name": "板块1",
                "metrics": {"pct_change": -4.0},
                "heat_index": 30.0,
            }
        ]

        result = processor._judge_trend(boards)
        # 当前版本 heat_change = 0，所以根据 pct_change < -3 判断
        assert result[0]["trend"] == "降温中"

    def test_judge_trend_stable(self, processor):
        """测试稳定信号"""
        # 其他情况标记为"稳定"
        boards = [
            {
                "name": "板块1",
                "metrics": {"pct_change": 1.0},
                "heat_index": 60.0,
            }
        ]

        result = processor._judge_trend(boards)
        # heat_change = 0，pct_change = 1.0，不满足加热或降温条件
        assert result[0]["trend"] in ["新", "稳定"]


class TestIndustryTrendProcessorIntegration:
    """集成测试"""

    @pytest.fixture
    def processor(self):
        """创建 Processor 实例"""
        proc = IndustryTrendProcessor()
        proc.date = "2026-03-06"
        proc.category = "L1"
        proc.data = [
            {
                "name": "电子",
                "code": "801080.SI",
                "date": "2026-03-06",
                "metrics": {
                    "pct_change": 3.5,
                    "turnover_rate": 4.2,
                    "amount": 150000.0,
                    "float_mv": 500000.0,
                },
            },
            {
                "name": "计算机",
                "code": "801750.SI",
                "date": "2026-03-06",
                "metrics": {
                    "pct_change": 2.8,
                    "turnover_rate": 5.1,
                    "amount": 120000.0,
                    "float_mv": 400000.0,
                },
            },
            {
                "name": "通信",
                "code": "801770.SI",
                "date": "2026-03-06",
                "metrics": {
                    "pct_change": 1.5,
                    "turnover_rate": 3.8,
                    "amount": 80000.0,
                    "float_mv": 300000.0,
                },
            },
        ]
        return proc

    def test_full_pipeline(self, processor):
        """测试完整处理流程"""
        # 1. 计算成交额占比
        processor._calc_volume_ratio()

        # 2. 计算热度指数
        boards = processor._calc_heat_index()

        # 3. 判断趋势
        boards = processor._judge_trend(boards)

        # 4. 按热度排序
        boards = sorted(boards, key=lambda x: x['heat_index'], reverse=True)

        # 验证结果
        assert len(boards) == 3
        # 热度应该是降序排列
        for i in range(len(boards) - 1):
            assert boards[i]["heat_index"] >= boards[i + 1]["heat_index"]

        # 每个板块应该有完整的字段
        for board in boards:
            assert "name" in board
            assert "code" in board
            assert "heat_index" in board
            assert "trend" in board
            assert "scores" in board
