# -*- coding: utf-8 -*-
"""测试 ConceptFetcherAkshare 数据转换逻辑"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from skills.industry_trend.scripts.concept_fetcher.akshare import ConceptFetcherAkshare


class TestConceptFetcherAkshareTransform:
    """测试 ConceptFetcherAkshare 的数据转换方法"""

    @pytest.fixture
    def fetcher(self):
        """创建 Fetcher 实例"""
        return ConceptFetcherAkshare()

    @pytest.fixture
    def sample_concept_data(self):
        """模拟概念板块数据"""
        return [
            {
                '板块名称': 'AI',
                '板块代码': 'BK0001',
                '最新价': 1234.56,
                '涨跌幅': 3.5,
                '涨跌额': 42.1,
                '成交量': 123456,
                '成交额': 1234567890,  # 元
                '换手率': 2.5,
                '上涨家数': 45,
                '下跌家数': 12,
                '领涨股票': 'XX科技',
                '领涨股票-涨跌幅': 9.8,
                '总市值': 5000000000,  # 元
            },
            {
                '板块名称': '芯片',
                '板块代码': 'BK0002',
                '最新价': 2345.67,
                '涨跌幅': 2.1,
                '涨跌额': 48.3,
                '成交量': 234567,
                '成交额': 2345678901,  # 元
                '换手率': 3.1,
                '上涨家数': 56,
                '下跌家数': 18,
                '领涨股票': 'YY电子',
                '领涨股票-涨跌幅': 7.5,
                '总市值': 6000000000,  # 元
            },
            {
                '板块名称': '机器人',
                '板块代码': 'BK0003',
                '最新价': 1567.89,
                '涨跌幅': -1.5,
                '涨跌额': -24.0,
                '成交量': 89000,
                '成交额': 890000000,  # 元
                '换手率': 1.8,
                '上涨家数': 20,
                '下跌家数': 35,
                '领涨股票': 'ZZ智能',
                '领涨股票-涨跌幅': 5.2,
                '总市值': 3000000000,  # 元
            },
        ]

    def test_transform_basic(self, fetcher, sample_concept_data):
        """测试基本数据转换"""
        result = fetcher._transform(sample_concept_data, '2026-03-06')

        # 验证数据条数
        assert len(result) == 3

        # 验证第一条数据
        first = result[0]
        assert first['name'] == 'AI'
        assert first['code'] == 'BK0001'
        assert first['date'] == '2026-03-06'

        # 验证 metrics
        assert first['metrics']['close'] == 1234.56
        assert first['metrics']['pct_change'] == 3.5
        assert first['metrics']['turnover_rate'] == 2.5
        assert first['metrics']['up_count'] == 45
        assert first['metrics']['down_count'] == 12

    def test_transform_amount_conversion(self, fetcher, sample_concept_data):
        """测试成交额单位转换（元 -> 万元）"""
        result = fetcher._transform(sample_concept_data, '2026-03-06')

        # 成交额：1234567890 元 -> 123456.789 万元
        assert abs(result[0]['metrics']['amount'] - 123456.789) < 1

    def test_transform_float_mv_conversion(self, fetcher, sample_concept_data):
        """测试市值单位转换（元 -> 万元）"""
        result = fetcher._transform(sample_concept_data, '2026-03-06')

        # 总市值：5000000000 元 -> 500000.0 万元
        assert result[0]['metrics']['float_mv'] == 500000.0

    def test_parse_float_valid(self, fetcher):
        """测试浮点数解析 - 正常值"""
        assert fetcher._parse_float(123.45) == 123.45
        assert fetcher._parse_float('456.78') == 456.78
        assert fetcher._parse_float(0) == 0.0

    def test_parse_float_invalid(self, fetcher):
        """测试浮点数解析 - 无效值"""
        assert fetcher._parse_float(None) == 0.0
        assert fetcher._parse_float('N/A') == 0.0
        assert fetcher._parse_float('abc') == 0.0

    def test_parse_int_valid(self, fetcher):
        """测试整数解析 - 正常值"""
        assert fetcher._parse_int(123) == 123
        assert fetcher._parse_int('456') == 456
        assert fetcher._parse_int(0) == 0

    def test_parse_int_invalid(self, fetcher):
        """测试整数解析 - 无效值"""
        assert fetcher._parse_int(None) == 0
        assert fetcher._parse_int('N/A') == 0
        assert fetcher._parse_int('abc') == 0

    def test_transform_empty_data(self, fetcher):
        """测试空数据情况"""
        result = fetcher._transform([], '2026-03-06')
        assert len(result) == 0

    def test_transform_missing_fields(self, fetcher):
        """测试缺失字段情况"""
        # 缺少必要字段的数据
        data = [
            {'板块名称': '', '板块代码': ''},  # 空名称和代码
            {'板块名称': 'AI', '板块代码': 'BK0001'},  # 正常数据
        ]

        result = fetcher._transform(data, '2026-03-06')

        # 只返回有效数据
        assert len(result) == 1
        assert result[0]['name'] == 'AI'
