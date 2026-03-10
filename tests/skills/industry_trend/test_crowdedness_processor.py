# -*- coding: utf-8 -*-
"""板块拥挤度指标 Processor 测试"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from openclaw_alpha.skills.industry_trend.crowdedness_processor.crowdedness_processor import (
    CrowdednessProcessor,
    CROWDEDNESS_WEIGHTS,
    CROWDEDNESS_LEVELS,
)


class TestCrowdednessProcessor:
    """拥挤度 Processor 测试"""
    
    @pytest.fixture
    def processor(self):
        """创建 Processor 实例"""
        return CrowdednessProcessor()
    
    @pytest.fixture
    def sample_industry_data(self):
        """示例行业数据"""
        return [
            {
                "name": "电子",
                "code": "801080",
                "metrics": {
                    "pct_change": 3.5,
                    "turnover_rate": 5.2,
                    "amount": 1000000000,  # 10亿
                }
            },
            {
                "name": "计算机",
                "code": "801750",
                "metrics": {
                    "pct_change": 2.1,
                    "turnover_rate": 4.0,
                    "amount": 800000000,  # 8亿
                }
            },
            {
                "name": "医药生物",
                "code": "801150",
                "metrics": {
                    "pct_change": 1.0,
                    "turnover_rate": 2.5,
                    "amount": 500000000,  # 5亿
                }
            },
        ]
    
    @pytest.fixture
    def sample_concept_data(self):
        """示例概念数据"""
        return [
            {
                "name": "人工智能",
                "code": "BK0001",
                "metrics": {
                    "pct_change": 5.0,
                    "turnover_rate": 8.0,
                    "amount": 2000000000,  # 20亿
                    "up_count": 80,
                    "down_count": 20,
                }
            },
            {
                "name": "新能源",
                "code": "BK0002",
                "metrics": {
                    "pct_change": 3.0,
                    "turnover_rate": 6.0,
                    "amount": 1500000000,  # 15亿
                    "up_count": 60,
                    "down_count": 40,
                }
            },
            {
                "name": "芯片",
                "code": "BK0003",
                "metrics": {
                    "pct_change": 2.0,
                    "turnover_rate": 4.0,
                    "amount": 1000000000,  # 10亿
                    "up_count": 50,
                    "down_count": 50,
                }
            },
        ]
    
    # ========== 分位数计算测试 ==========
    
    def test_calc_percentile_basic(self, processor):
        """测试基本分位数计算"""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        percentiles = processor._calc_percentile(values)
        
        assert len(percentiles) == 5
        assert percentiles[0] == 0.0   # 1.0 是最小值
        assert percentiles[4] == 100.0  # 5.0 是最大值
        assert percentiles[2] == 50.0   # 3.0 是中位数
    
    def test_calc_percentile_single_value(self, processor):
        """测试单个值的分位数"""
        values = [5.0]
        percentiles = processor._calc_percentile(values)
        
        assert percentiles == [100.0]
    
    def test_calc_percentile_empty(self, processor):
        """测试空列表"""
        percentiles = processor._calc_percentile([])
        assert percentiles == []
    
    def test_calc_percentile_equal_values(self, processor):
        """测试所有值相同"""
        values = [3.0, 3.0, 3.0]
        percentiles = processor._calc_percentile(values)
        
        assert len(percentiles) == 3
        assert percentiles[0] == 0.0
        assert percentiles[1] == 50.0
        assert percentiles[2] == 100.0
    
    def test_calc_percentile_with_duplicates(self, processor):
        """测试有重复值的分位数"""
        values = [1.0, 2.0, 2.0, 3.0]
        percentiles = processor._calc_percentile(values)
        
        assert len(percentiles) == 4
        assert percentiles[0] == 0.0   # 1.0 最小
        assert percentiles[3] == 100.0  # 3.0 最大
    
    # ========== 拥挤度等级判断测试 ==========
    
    def test_judge_crowdedness_level_high(self, processor):
        """测试高拥挤度"""
        assert processor._judge_crowdedness_level(85.0) == "高拥挤"
        assert processor._judge_crowdedness_level(100.0) == "高拥挤"
        assert processor._judge_crowdedness_level(80.1) == "高拥挤"
    
    def test_judge_crowdedness_level_medium(self, processor):
        """测试中等拥挤度"""
        assert processor._judge_crowdedness_level(65.0) == "中等拥挤"
        assert processor._judge_crowdedness_level(80.0) == "中等拥挤"
        assert processor._judge_crowdedness_level(50.1) == "中等拥挤"
    
    def test_judge_crowdedness_level_low(self, processor):
        """测试低拥挤度"""
        assert processor._judge_crowdedness_level(30.0) == "低拥挤"
        assert processor._judge_crowdedness_level(50.0) == "低拥挤"
        assert processor._judge_crowdedness_level(0.0) == "低拥挤"
    
    # ========== 成交额占比计算测试 ==========
    
    def test_calc_volume_ratio(self, processor, sample_industry_data):
        """测试成交额占比计算"""
        processor.data = sample_industry_data
        processor._calc_volume_ratio()
        
        # 总成交额 = 10 + 8 + 5 = 23亿
        # 电子：10/23 ≈ 43.48%
        # 计算机：8/23 ≈ 34.78%
        # 医药生物：5/23 ≈ 21.74%
        
        assert abs(processor.data[0]['metrics']['volume_ratio'] - 43.478) < 0.1
        assert abs(processor.data[1]['metrics']['volume_ratio'] - 34.783) < 0.1
        assert abs(processor.data[2]['metrics']['volume_ratio'] - 21.739) < 0.1
    
    def test_calc_volume_ratio_zero_total(self, processor):
        """测试总成交额为 0"""
        processor.data = [
            {"name": "A", "code": "001", "metrics": {"amount": 0}},
            {"name": "B", "code": "002", "metrics": {"amount": 0}},
        ]
        processor._calc_volume_ratio()
        
        assert processor.data[0]['metrics']['volume_ratio'] == 0.0
        assert processor.data[1]['metrics']['volume_ratio'] == 0.0
    
    # ========== 拥挤度计算测试 ==========
    
    def test_calc_crowdedness_basic(self, processor, sample_industry_data):
        """测试拥挤度基本计算"""
        processor.data = sample_industry_data
        processor._calc_volume_ratio()
        boards = processor._calc_crowdedness()
        
        assert len(boards) == 3
        
        # 电子：换手率最高（5.2），成交额占比最高 → 拥挤度最高
        electronic = next(b for b in boards if b['name'] == '电子')
        assert electronic['crowdedness'] > 80
        assert electronic['level'] == "高拥挤"
        
        # 医药生物：换手率最低（2.5），成交额占比最低 → 拥挤度最低
        medical = next(b for b in boards if b['name'] == '医药生物')
        assert medical['crowdedness'] < 50
        assert medical['level'] == "低拥挤"
    
    def test_calc_crowdedness_details(self, processor, sample_industry_data):
        """测试拥挤度详情字段"""
        processor.data = sample_industry_data
        processor._calc_volume_ratio()
        boards = processor._calc_crowdedness()
        
        board = boards[0]
        
        # 检查必要字段
        assert 'name' in board
        assert 'code' in board
        assert 'crowdedness' in board
        assert 'level' in board
        assert 'details' in board
        
        # 检查详情字段
        assert 'turnover_rate' in board['details']
        assert 'turnover_percentile' in board['details']
        assert 'volume_ratio' in board['details']
        assert 'volume_percentile' in board['details']
    
    # ========== 完整流程测试 ==========
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_process_industry(self, processor, sample_industry_data, tmp_path):
        """测试行业数据处理完整流程"""
        with patch.object(processor, '_fetch_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_industry_data
            
            # Mock 输出路径
            with patch('skills.industry_trend.scripts.crowdedness_processor.crowdedness_processor.get_output_path') as mock_path:
                mock_path.return_value = tmp_path / "crowdedness.json"
                
                result = await processor.process(
                    category="L1",
                    date="2026-03-08",
                    top_n=10,
                )
        
        # 验证结果结构
        assert result['date'] == "2026-03-08"
        assert result['category'] == "L1"
        assert len(result['boards']) == 3
        
        # 验证排序（按拥挤度降序）
        crowdedness_values = [b['crowdedness'] for b in result['boards']]
        assert crowdedness_values == sorted(crowdedness_values, reverse=True)
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_process_concept(self, processor, sample_concept_data, tmp_path):
        """测试概念板块数据处理"""
        with patch.object(processor, '_fetch_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_concept_data
            
            with patch('skills.industry_trend.scripts.crowdedness_processor.crowdedness_processor.get_output_path') as mock_path:
                mock_path.return_value = tmp_path / "crowdedness.json"
                
                result = await processor.process(
                    category="concept",
                    date="2026-03-08",
                    top_n=5,
                )
        
        assert result['category'] == "concept"
        assert len(result['boards']) == 3
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_process_top_n_filtering(self, processor, sample_industry_data, tmp_path):
        """测试 Top N 过滤"""
        with patch.object(processor, '_fetch_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_industry_data
            
            with patch('skills.industry_trend.scripts.crowdedness_processor.crowdedness_processor.get_output_path') as mock_path:
                mock_path.return_value = tmp_path / "crowdedness.json"
                
                result = await processor.process(
                    category="L1",
                    date="2026-03-08",
                    top_n=2,  # 只返回 Top 2
                )
        
        assert len(result['boards']) == 2
    
    # ========== 权重常量测试 ==========
    
    def test_weights_sum_to_one(self):
        """测试权重之和为 1"""
        total = sum(CROWDEDNESS_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001
    
    def test_crowdedness_levels_order(self):
        """测试拥挤度等级阈值顺序"""
        # high > medium > low
        assert CROWDEDNESS_LEVELS["high"][0] > CROWDEDNESS_LEVELS["medium"][0]
        assert CROWDEDNESS_LEVELS["medium"][0] > CROWDEDNESS_LEVELS["low"][0]
