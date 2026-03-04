# -*- coding: utf-8 -*-
"""概念板块行情查询测试"""

from unittest.mock import AsyncMock, patch

from datetime import datetime

import pandas as pd
import pytest

from openclaw_alpha.commands.board_concept import get_concept_board_data
from openclaw_alpha.core.data_source import DataSource
from openclaw_alpha.core.fetcher_registry import FetcherRegistry
from openclaw_alpha.core.registry import DataSourceRegistry
from openclaw_alpha.fetchers.concept_board import (
    ConceptBoardAkshareFetcher,
)
from openclaw_alpha.fetchers.concept_board.models import (
    ConceptBoardFetchParams,
    ConceptBoardFetchResult,
    ConceptBoardItem,
)


class MockAkshareDataSource(DataSource[str]):
    """测试用 Akshare 数据源"""

    @property
    def name(self) -> str:
        return "akshare"

    @property
    def required_config(self) -> list[str]:
        return []

    async def initialize(self) -> None:
        self._client = "akshare_client"


@pytest.fixture
def mock_concept_board_result() -> ConceptBoardFetchResult:
    """构造模拟的概念板块获取结果"""
    return ConceptBoardFetchResult(
        trade_date="2026-03-04",
        data_source="东方财富",
        items=[
            ConceptBoardItem(
                rank=1,
                board_code="BK0891",
                board_name="人工智能",
                price=1250.5,
                change_pct=3.52,
                change=42.5,
                volume=125.6,
                amount=250500000000,
                turnover_rate=3.21,
                up_count=45,
                down_count=5,
                leader_name="科大讯飞",
                leader_change=5.23,
                total_mv=890500000.0,
            ),
            ConceptBoardItem(
                rank=2,
                board_code="BK0892",
                board_name="新能源车",
                price=980.3,
                change_pct=2.15,
                change=20.8,
                volume=98.3,
                amount=180200000.0,
                turnover_rate=2.56,
                up_count=32,
                down_count=8,
                leader_name="比亚迪",
                leader_change=4.12,
                total_mv=650200000.0,
            ),
            ConceptBoardItem(
                rank=3,
                board_code="BK0893",
                board_name="芯片",
                price=760.2,
                change_pct=1.88,
                change=14.2,
                volume=76.2,
                amount=120800000.0,
                turnover_rate=1.89,
                up_count=28,
                down_count=12,
                leader_name="中芯国际",
                leader_change=3.56,
                total_mv=420800000.0,
            ),
        ],
    )


class TestGetConceptBoardData:
    """get_concept_board_data 函数测试"""

    def setup_method(self) -> None:
        """每个测试前重置注册表"""
        FetcherRegistry.get_instance().reset()
        DataSourceRegistry.get_instance().reset()

        # 注册数据源
        DataSourceRegistry.get_instance().register(MockAkshareDataSource)

        # 注册 Fetcher
        FetcherRegistry.get_instance().register(ConceptBoardAkshareFetcher())

    def test_success(self, mock_concept_board_result: ConceptBoardFetchResult) -> None:
        """测试成功获取概念板块数据"""
        fetcher = FetcherRegistry.get_instance().get("akshare_concept")
        with patch.object(
            fetcher, "fetch", new_callable=AsyncMock, return_value=mock_concept_board_result
        ):
            result = get_concept_board_data(top=20, sort_by="change_pct")

        assert result["success"] is True
        assert "timestamp" in result
        assert "trade_date" in result
        assert result["count"] == 3
        assert len(result["data"]) == 3
        assert result["data_source"] == "东方财富"

    def test_sort_by_amount(self, mock_concept_board_result: ConceptBoardFetchResult) -> None:
        """测试按成交额排序"""
        # 修改结果只返回1个元素
        limited_result = ConceptBoardFetchResult(
            trade_date=mock_concept_board_result.trade_date,
            data_source=mock_concept_board_result.data_source,
            items=mock_concept_board_result.items[:2],
        )
        fetcher = FetcherRegistry.get_instance().get("akshare_concept")
        with patch.object(
            fetcher, "fetch", new_callable=AsyncMock, return_value=limited_result
        ):
            result = get_concept_board_data(top=20, sort_by="amount")

        assert result["count"] == 1
        assert len(result["data"]) == 1

    def test_sort_by_change_pct(self, mock_concept_board_result: ConceptBoardFetchResult) -> None:
        """测试按涨跌幅排序"""
        fetcher = FetcherRegistry.get_instance().get("akshare_concept")
        with patch.object(
            fetcher, "fetch", new_callable=AsyncMock, return_value=mock_concept_board_result
        ):
            result = get_concept_board_data(top=20, sort_by="change_pct")

        assert result["data"][0]["board_name"] == "人工智能"
        assert result["data"][0]["change_pct"] == 3.52

    def test_sort_by_amount(self, mock_concept_board_result: ConceptBoardFetchResult) -> None:
        """测试按成交额排序"""
        fetcher = FetcherRegistry.get_instance().get("akshare_concept")
        with patch.object(
            fetcher, "fetch", new_callable=AsyncMock, return_value=mock_concept_board_result
        ):
            result = get_concept_board_data(top=20, sort_by="amount")

        assert result["data"][0]["board_name"] == "人工智能"
        assert result["data"][0]["amount"] == 250500000.0
    def test_data_fields(self, mock_concept_board_result: ConceptBoardFetchResult) -> None:
        """测试返回数据包含必需字段"""
        fetcher = FetcherRegistry.get_instance().get("akshare_concept")
        with patch.object(
            fetcher, "fetch", new_callable=AsyncMock, return_value=mock_concept_board_result
        ):
            result = get_concept_board_data(top=20, sort_by="change_pct")

        item = result["data"][0]
        required_fields = [
            "rank",
            "board_code",
            "board_name",
            "price",
            "change_pct",
            "change",
            "volume",
            "amount",
            "turnover_rate",
            "up_count",
            "down_count",
            "leader_name",
            "leader_change",
            "total_mv",
        ]
        for field in required_fields:
            assert field in item, f"缺少必需字段: {field}"

    def test_empty_result(self) -> None:
        """测试空结果返回失败"""
        empty_result = ConceptBoardFetchResult(
            trade_date="2026-03-04",
            data_source="东方财富",
            items=[],
        )

        fetcher = FetcherRegistry.get_instance().get("akshare_concept")
        with patch.object(
            fetcher, "fetch", new_callable=AsyncMock, return_value=empty_result
        ):
            result = get_concept_board_data(top=20, sort_by="change_pct")

        assert result["success"] is True
        assert result["count"] == 0
        assert len(result["data"]) == 0

    def test_exception_handling(self) -> None:
        """测试异常处理"""
        fetcher = FetcherRegistry.get_instance().get("akshare_concept")
        with patch.object(
            fetcher,
            "fetch",
            new_callable=AsyncMock,
            side_effect=Exception("网络错误"),
        ):
            result = get_concept_board_data(top=20, sort_by="change_pct")

        assert result["success"] is False
        assert "网络错误" in result["error"]
