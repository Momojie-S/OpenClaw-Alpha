# -*- coding: utf-8 -*-
"""行业轮动综合评分 Processor 测试"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from openclaw_alpha.skills.industry_trend.rotation_score_processor.rotation_score_processor import (
    RotationScoreProcessor,
    SCORE_LEVELS,
    GOLDEN_COMBO,
)


class TestRotationScoreProcessor:
    """轮动评分 Processor 测试"""
    
    @pytest.fixture
    def processor(self):
        """创建 Processor 实例"""
        return RotationScoreProcessor()
    
    @pytest.fixture
    def sample_heat_data(self):
        """示例热度数据"""
        return {
            "date": "2026-03-08",
            "category": "L1",
            "boards": [
                {
                    "name": "电子",
                    "code": "801080",
                    "heat_index": 85.0,
                    "trend": "加热中",
                    "metrics": {"pct_change": 3.5},
                },
                {
                    "name": "计算机",
                    "code": "801750",
                    "heat_index": 65.0,
                    "trend": "稳定",
                    "metrics": {"pct_change": 1.2},
                },
                {
                    "name": "银行",
                    "code": "801780",
                    "heat_index": 40.0,
                    "trend": "降温中",
                    "metrics": {"pct_change": -0.5},
                },
            ],
        }
    
    @pytest.fixture
    def sample_crowdedness_data(self):
        """示例拥挤度数据"""
        return {
            "date": "2026-03-08",
            "category": "L1",
            "boards": [
                {"name": "电子", "crowdedness": 80.0},
                {"name": "计算机", "crowdedness": 35.0},
                {"name": "银行", "crowdedness": 25.0},
            ],
        }
    
    # ========== 评分等级判断测试 ==========
    
    def test_judge_score_level_a_plus(self, processor):
        """测试 A+ 等级"""
        assert processor._judge_score_level(75.0) == "黄金机会"
        assert processor._judge_score_level(100.0) == "黄金机会"
        assert processor._judge_score_level(70.1) == "黄金机会"
    
    def test_judge_score_level_a(self, processor):
        """测试 A 等级"""
        assert processor._judge_score_level(60.0) == "优质机会"
        assert processor._judge_score_level(70.0) == "优质机会"
        assert processor._judge_score_level(50.1) == "优质机会"
    
    def test_judge_score_level_b(self, processor):
        """测试 B 等级"""
        assert processor._judge_score_level(40.0) == "一般机会"
        assert processor._judge_score_level(50.0) == "一般机会"
        assert processor._judge_score_level(30.1) == "一般机会"
    
    def test_judge_score_level_c(self, processor):
        """测试 C 等级"""
        assert processor._judge_score_level(20.0) == "风险机会"
        assert processor._judge_score_level(30.0) == "风险机会"
        assert processor._judge_score_level(0.0) == "风险机会"
    
    # ========== 轮动评分计算测试 ==========
    
    def test_calc_rotation_score_basic(self, processor, sample_heat_data, sample_crowdedness_data):
        """测试轮动评分基本计算"""
        processor.heat_data = sample_heat_data
        processor.crowdedness_data = sample_crowdedness_data
        boards = processor._calc_rotation_score()
        
        assert len(boards) == 3
        
        # 电子：热度 85，拥挤度 80
        # 轮动评分 = 85 × (100 - 80) / 100 = 17
        electronic = next(b for b in boards if b['name'] == '电子')
        assert electronic['rotation_score'] == 17.0
        assert electronic['is_golden'] == False  # 高热度但高拥挤度
        
        # 计算机：热度 65，拥挤度 35
        # 轮动评分 = 65 × (100 - 35) / 100 = 42.25
        computer = next(b for b in boards if b['name'] == '计算机')
        assert computer['rotation_score'] == 42.25
        assert computer['is_golden'] == True  # 黄金组合！
        
        # 银行：热度 40，拥挤度 25
        # 轮动评分 = 40 × (100 - 25) / 100 = 30
        bank = next(b for b in boards if b['name'] == '银行')
        assert bank['rotation_score'] == 30.0
        assert bank['is_golden'] == False  # 低热度
    
    def test_calc_rotation_score_details(self, processor, sample_heat_data, sample_crowdedness_data):
        """测试轮动评分详情字段"""
        processor.heat_data = sample_heat_data
        processor.crowdedness_data = sample_crowdedness_data
        boards = processor._calc_rotation_score()
        
        board = boards[0]
        
        # 检查必要字段
        assert 'name' in board
        assert 'code' in board
        assert 'rotation_score' in board
        assert 'level' in board
        assert 'is_golden' in board
        assert 'details' in board
        
        # 检查详情字段
        assert 'heat_index' in board['details']
        assert 'crowdedness' in board['details']
        assert 'trend' in board['details']
        assert 'pct_change' in board['details']
    
    def test_calc_rotation_score_missing_crowdedness(self, processor, sample_heat_data):
        """测试缺少拥挤度数据时的默认值"""
        processor.heat_data = sample_heat_data
        processor.crowdedness_data = {"boards": []}  # 无拥挤度数据
        boards = processor._calc_rotation_score()
        
        # 应该使用默认拥挤度 50
        assert len(boards) == 3
        for board in boards:
            assert board['details']['crowdedness'] == 50
    
    # ========== 黄金组合判断测试 ==========
    
    def test_golden_combo_high_heat_low_crowdedness(self, processor, sample_heat_data, sample_crowdedness_data):
        """测试黄金组合：高热度 + 低拥挤度"""
        # 修改计算机的热度到 65（>60），拥挤度 35（<40）
        processor.heat_data = sample_heat_data
        processor.crowdedness_data = sample_crowdedness_data
        boards = processor._calc_rotation_score()
        
        computer = next(b for b in boards if b['name'] == '计算机')
        assert computer['details']['heat_index'] > GOLDEN_COMBO["heat_threshold"]
        assert computer['details']['crowdedness'] < GOLDEN_COMBO["crowdedness_threshold"]
        assert computer['is_golden'] == True
    
    def test_golden_combo_not_golden_cases(self, processor):
        """测试非黄金组合的情况"""
        # 高热度 + 高拥挤度
        processor.heat_data = {
            "boards": [{"name": "A", "code": "001", "heat_index": 80, "trend": "", "metrics": {}}]
        }
        processor.crowdedness_data = {
            "boards": [{"name": "A", "crowdedness": 70}]
        }
        boards = processor._calc_rotation_score()
        assert boards[0]['is_golden'] == False
        
        # 低热度 + 低拥挤度
        processor.heat_data = {
            "boards": [{"name": "B", "code": "002", "heat_index": 50, "trend": "", "metrics": {}}]
        }
        processor.crowdedness_data = {
            "boards": [{"name": "B", "crowdedness": 30}]
        }
        boards = processor._calc_rotation_score()
        assert boards[0]['is_golden'] == False
    
    # ========== 完整流程测试 ==========
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_process_with_existing_data(self, processor, sample_heat_data, sample_crowdedness_data, tmp_path):
        """测试使用已有数据的完整流程"""
        with patch('openclaw_alpha.skills.industry_trend.rotation_score_processor.rotation_score_processor.load_output') as mock_load:
            mock_load.side_effect = [sample_heat_data, sample_crowdedness_data]
            
            with patch('openclaw_alpha.skills.industry_trend.rotation_score_processor.rotation_score_processor.get_output_path') as mock_path:
                mock_path.return_value = tmp_path / "rotation_score.json"
                
                result = await processor.process(
                    category="L1",
                    date="2026-03-08",
                    top_n=10,
                )
        
        # 验证结果结构
        assert result['date'] == "2026-03-08"
        assert result['category'] == "L1"
        assert len(result['boards']) == 3
        
        # 验证排序（按轮动评分降序）
        scores = [b['rotation_score'] for b in result['boards']]
        assert scores == sorted(scores, reverse=True)
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_process_top_n_filtering(self, processor, sample_heat_data, sample_crowdedness_data, tmp_path):
        """测试 Top N 过滤"""
        with patch('openclaw_alpha.skills.industry_trend.rotation_score_processor.rotation_score_processor.load_output') as mock_load:
            mock_load.side_effect = [sample_heat_data, sample_crowdedness_data]
            
            with patch('openclaw_alpha.skills.industry_trend.rotation_score_processor.rotation_score_processor.get_output_path') as mock_path:
                mock_path.return_value = tmp_path / "rotation_score.json"
                
                result = await processor.process(
                    category="L1",
                    date="2026-03-08",
                    top_n=2,  # 只返回 Top 2
                )
        
        assert len(result['boards']) == 2
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_process_no_heat_data(self, processor, tmp_path):
        """测试无热度数据时的错误处理"""
        # Mock load_output 返回 None，并 mock 获取数据的方法也返回 None
        with patch('openclaw_alpha.skills.industry_trend.rotation_score_processor.rotation_score_processor.load_output') as mock_load:
            mock_load.return_value = None
            
            # Mock 获取数据的方法
            processor._fetch_and_calc_heat = AsyncMock(return_value=None)
            processor._fetch_and_calc_crowdedness = AsyncMock(return_value=None)
            
            result = await processor.process(
                category="L1",
                date="2026-03-08",
                top_n=10,
            )
        
        assert 'error' in result
        assert result['boards'] == []
    
    # ========== 常量测试 ==========
    
    def test_score_levels_order(self):
        """测试评分等级阈值顺序"""
        # A+ > A > B > C
        assert SCORE_LEVELS["A+"][0] > SCORE_LEVELS["A"][0]
        assert SCORE_LEVELS["A"][0] > SCORE_LEVELS["B"][0]
        assert SCORE_LEVELS["B"][0] > SCORE_LEVELS["C"][0]
    
    def test_golden_combo_thresholds(self):
        """测试黄金组合阈值"""
        # 热度阈值应该大于 0
        assert GOLDEN_COMBO["heat_threshold"] > 0
        # 拥挤度阈值应该小于 100
        assert GOLDEN_COMBO["crowdedness_threshold"] < 100
        # 拥挤度阈值应该小于热度阈值（低拥挤度更容易）
        assert GOLDEN_COMBO["crowdedness_threshold"] < GOLDEN_COMBO["heat_threshold"]
