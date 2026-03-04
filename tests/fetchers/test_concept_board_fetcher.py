# -*- coding: utf-8 -*-
"""ConceptBoard Fetcher 测试"""

import pandas as pd

from openclaw_alpha.fetchers.concept_board import (
    ConceptBoardAkshareFetcher,
    ConceptBoardFetchParams,
    ConceptBoardItem,
)


class TestConceptBoardFetchParams:
    """ConceptBoardFetchParams 测试"""

    def test_default_params(self) -> None:
        """测试默认参数"""
        params = ConceptBoardFetchParams()
        assert params.top == 20
        assert params.sort_by == "change_pct"

    def test_custom_params(self) -> None:
        """测试自定义参数"""
        params = ConceptBoardFetchParams(top=50, sort_by="amount")
        assert params.top == 50
        assert params.sort_by == "amount"


class TestConceptBoardItem:
    """ConceptBoardItem 测试"""

    def test_item_creation(self) -> None:
        """测试创建数据项"""
        item = ConceptBoardItem(
            rank=1,
            board_code="BK0001",
            board_name="测试板块",
            price=100.0,
            change_pct=5.5,
            change=5.0,
            volume=10000.0,
            amount=1000000.0,
            turnover_rate=3.5,
            up_count=50,
            down_count=10,
            leader_name="领涨股",
            leader_change=10.0,
            total_mv=10000000000.0,
        )

        assert item.rank == 1
        assert item.board_code == "BK0001"
        assert item.board_name == "测试板块"
        assert item.change_pct == 5.5


class TestConceptBoardAkshareFetcherTransform:
    """ConceptBoardAkshareFetcher 数据转换测试"""

    def test_parse_row_basic(self) -> None:
        """测试基本数据行解析"""
        # 模拟 DataFrame 行数据
        row_data = {
            "板块代码": "BK0001",
            "板块名称": "人工智能",
            "最新价": 100.5,
            "涨跌幅": 5.5,
            "涨跌额": 5.25,
            "总成交量": 10000,
            "总成交额": 1000000,
            "换手率": 3.5,
            "上涨家数": 50,
            "下跌家数": 10,
            "领涨股票": "股票A",
            "领涨股票_涨跌幅": 10.0,
            "总市值": 10000000000,
        }
        df = pd.DataFrame([row_data])
        row = df.itertuples(index=False).__next__()

        fetcher = ConceptBoardAkshareFetcher()
        item = fetcher._parse_row(1, row)

        assert item.rank == 1
        assert item.board_code == "BK0001"
        assert item.board_name == "人工智能"
        assert item.price == 100.5
        assert item.change_pct == 5.5
        assert item.up_count == 50
        assert item.down_count == 10

    def test_parse_row_with_none_values(self) -> None:
        """测试包含 None 值的数据行解析"""
        row_data = {
            "板块代码": "BK0002",
            "板块名称": "测试板块",
            "最新价": None,
            "涨跌幅": None,
            "涨跌额": None,
            "总成交量": 0,
            "总成交额": 0,
            "换手率": None,
            "上涨家数": None,
            "下跌家数": None,
            "领涨股票": "",
            "领涨股票_涨跌幅": None,
            "总市值": None,
        }
        df = pd.DataFrame([row_data])
        row = df.itertuples(index=False).__next__()

        fetcher = ConceptBoardAkshareFetcher()
        item = fetcher._parse_row(2, row)

        assert item.rank == 2
        assert item.board_code == "BK0002"
        assert item.price == 0.0
        assert item.change_pct == 0.0
        assert item.up_count == 0
        assert item.down_count == 0
