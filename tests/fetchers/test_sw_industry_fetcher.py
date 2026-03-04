# -*- coding: utf-8 -*-
"""SwIndustry Fetcher 测试"""

import pandas as pd

from openclaw_alpha.fetchers.sw_industry import (
    SwIndustryFetchParams,
    SwIndustryTushareFetcher,
)
from openclaw_alpha.fetchers.sw_industry.models import SwIndustryItem


class TestSwIndustryFetchParams:
    """SwIndustryFetchParams 测试"""

    def test_default_params(self) -> None:
        """测试默认参数"""
        params = SwIndustryFetchParams()
        assert params.trade_date is None
        assert params.level == "L3"
        assert params.top == 50
        assert params.sort_by == "change_pct"

    def test_custom_params(self) -> None:
        """测试自定义参数"""
        params = SwIndustryFetchParams(
            trade_date="20260303",
            level="L1",
            top=20,
            sort_by="amount",
        )
        assert params.trade_date == "20260303"
        assert params.level == "L1"
        assert params.top == 20
        assert params.sort_by == "amount"


class TestSwIndustryItem:
    """SwIndustryItem 测试"""

    def test_item_creation(self) -> None:
        """测试创建数据项"""
        item = SwIndustryItem(
            rank=1,
            board_code="850001.SI",
            board_name="测试行业",
            change_pct=5.5,
            close=1000.0,
            volume=100.0,
            amount=10.0,
            turnover_rate=3.5,
            float_mv=1000.0,
            total_mv=2000.0,
            pe=15.0,
            pb=1.5,
        )

        assert item.rank == 1
        assert item.board_code == "850001.SI"
        assert item.board_name == "测试行业"
        assert item.change_pct == 5.5


class TestSwIndustryTushareFetcherTransform:
    """SwIndustryTushareFetcher 数据转换测试"""

    def test_calculate_turnover_rate(self) -> None:
        """测试换手率计算"""
        df = pd.DataFrame({
            "amount": [1000000],  # 千元
            "float_mv": [10000000],  # 万元
        })

        fetcher = SwIndustryTushareFetcher()
        result = fetcher._calculate_turnover_rate(df)

        # 换手率 = (1000000 * 1000) / (10000000 * 10000) * 100 = 1.0
        assert result["turnover_rate"].iloc[0] == 1.0

    def test_calculate_turnover_rate_zero_float_mv(self) -> None:
        """测试流通市值为零时的换手率计算"""
        df = pd.DataFrame({
            "amount": [1000000],
            "float_mv": [0],
        })

        fetcher = SwIndustryTushareFetcher()
        result = fetcher._calculate_turnover_rate(df)

        assert result["turnover_rate"].iloc[0] == 0

    def test_filter_by_level_l1(self) -> None:
        """测试一级行业筛选"""
        df = pd.DataFrame({
            "ts_code": ["801001.SI", "850001.SI"],
            "name": ["一级行业", "三级行业"],
        })

        fetcher = SwIndustryTushareFetcher()
        result = fetcher._filter_by_level(df, "L1")

        assert len(result) == 1
        assert result["ts_code"].iloc[0] == "801001.SI"

    def test_filter_by_level_l3(self) -> None:
        """测试三级行业筛选"""
        df = pd.DataFrame({
            "ts_code": ["801001.SI", "850001.SI", "850002.SI"],
            "name": ["一级行业", "三级行业A", "三级行业B"],
        })

        fetcher = SwIndustryTushareFetcher()
        result = fetcher._filter_by_level(df, "L3")

        assert len(result) == 2
        assert all(result["ts_code"].str.startswith("85"))

    def test_parse_row(self) -> None:
        """测试数据行解析和单位转换"""
        row_data = {
            "ts_code": "850001.SI",
            "name": "测试行业",
            "close": 1000.0,
            "pct_change": 5.5,
            "vol": 1000000,  # 手
            "amount": 1000000,  # 千元
            "float_mv": 10000000,  # 万元
            "total_mv": 20000000,  # 万元
            "pe": 15.0,
            "pb": 1.5,
        }
        df = pd.DataFrame([row_data])
        df = df.assign(turnover_rate=1.0)  # 预计算换手率
        row = df.itertuples(index=False).__next__()

        fetcher = SwIndustryTushareFetcher()
        item = fetcher._parse_row(1, row)

        assert item.rank == 1
        assert item.board_code == "850001.SI"
        assert item.board_name == "测试行业"
        assert item.volume == 100.0  # 手 -> 万手 (1000000 / 10000)
        assert item.amount == 10.0  # 千元 -> 亿元 (1000000 * 1000 / 100000000)
        assert item.float_mv == 1000.0  # 万元 -> 亿
        assert item.total_mv == 2000.0  # 万元 -> 亿
