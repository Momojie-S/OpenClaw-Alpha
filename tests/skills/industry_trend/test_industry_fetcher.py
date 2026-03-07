# -*- coding: utf-8 -*-
"""测试 IndustryFetcherTushare 数据转换逻辑"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from skills.industry_trend.scripts.industry_fetcher.tushare import IndustryFetcherTushare


class TestIndustryFetcherTushareTransform:
    """测试 IndustryFetcherTushare 的数据转换方法"""

    @pytest.fixture
    def fetcher(self):
        """创建 Fetcher 实例"""
        return IndustryFetcherTushare()

    @pytest.fixture
    def sample_classifications(self):
        """模拟分类数据"""
        return [
            {
                'index_code': '801010.SI',
                'industry_name': '农林牧渔',
                'level': 'L1',
                'industry_code': '110000',
                'is_pub': '1',
            },
            {
                'index_code': '801030.SI',
                'industry_name': '基础化工',
                'level': 'L1',
                'industry_code': '220000',
                'is_pub': '1',
            },
            {
                'index_code': '801040.SI',
                'industry_name': '钢铁',
                'level': 'L1',
                'industry_code': '230000',
                'is_pub': '1',
            },
        ]

    @pytest.fixture
    def sample_daily_data(self):
        """模拟日线数据"""
        return [
            {
                'ts_code': '801010.SI',
                'trade_date': '20260306',
                'name': '农林牧渔',
                'close': 2946.60,
                'pct_change': 3.5,
                'amount': 83532.0,  # 万元
                'float_mv': 123456.0,  # 万元
            },
            {
                'ts_code': '801030.SI',
                'trade_date': '20260306',
                'name': '基础化工',
                'close': 3500.0,
                'pct_change': 2.1,
                'amount': 150000.0,
                'float_mv': 500000.0,
            },
            {
                'ts_code': '801040.SI',
                'trade_date': '20260306',
                'name': '钢铁',
                'close': 2100.0,
                'pct_change': -1.5,
                'amount': 80000.0,
                'float_mv': 300000.0,
            },
        ]

    def test_merge_data_basic(self, fetcher, sample_classifications, sample_daily_data):
        """测试基本数据合并"""
        result = fetcher._merge_data(
            sample_classifications,
            sample_daily_data,
            'L1',
            '2026-03-06',
        )

        # 验证数据条数
        assert len(result) == 3

        # 验证第一条数据
        first = result[0]
        assert first['name'] == '农林牧渔'
        assert first['code'] == '801010.SI'
        assert first['level'] == 'L1'
        assert first['date'] == '2026-03-06'

        # 验证 metrics
        assert first['metrics']['close'] == 2946.60
        assert first['metrics']['pct_change'] == 3.5
        assert first['metrics']['amount'] == 83532.0
        assert first['metrics']['float_mv'] == 123456.0

    def test_calc_turnover_rate(self, fetcher):
        """测试换手率计算"""
        # 正常情况
        daily = {'amount': 100000.0, 'float_mv': 500000.0}
        rate = fetcher._calc_turnover_rate(daily)
        assert rate == 20.0  # 100000 / 500000 * 100

        # 流通市值为 0
        daily = {'amount': 100000.0, 'float_mv': 0.0}
        rate = fetcher._calc_turnover_rate(daily)
        assert rate == 0.0

    def test_merge_data_missing_daily(self, fetcher, sample_classifications):
        """测试日线数据缺失的情况"""
        # 只有一条日线数据
        daily_data = [
            {
                'ts_code': '801010.SI',
                'trade_date': '20260306',
                'name': '农林牧渔',
                'close': 2946.60,
                'pct_change': 3.5,
                'amount': 83532.0,
                'float_mv': 123456.0,
            },
        ]

        result = fetcher._merge_data(
            sample_classifications,
            daily_data,
            'L1',
            '2026-03-06',
        )

        # 只返回有日线数据的板块
        assert len(result) == 1
        assert result[0]['name'] == '农林牧渔'

    def test_merge_data_empty(self, fetcher):
        """测试空数据情况"""
        result = fetcher._merge_data([], [], 'L1', '2026-03-06')
        assert len(result) == 0
