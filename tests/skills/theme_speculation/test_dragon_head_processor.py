# -*- coding: utf-8 -*-
"""龙头识别 Processor 测试"""

import pytest
from unittest.mock import AsyncMock, patch

from openclaw_alpha.skills.theme_speculation.dragon_head_processor.dragon_head_processor import (
    DragonHeadProcessor,
    DragonStock,
    DragonHeadResult,
)
from openclaw_alpha.skills.limit_up_tracker.limit_up_fetcher.models import (
    LimitUpItem,
    LimitUpType,
)


def create_limit_up_item(
    code: str,
    name: str,
    continuous: int = 3,
    first_limit_time: str = "09:35:00",
    float_mv: float = 100.0,
) -> LimitUpItem:
    """创建涨停股数据（测试辅助函数）"""
    return LimitUpItem(
        code=code,
        name=name,
        continuous=continuous,
        first_limit_time=first_limit_time,
        last_limit_time=first_limit_time,
        float_mv=float_mv,
        total_mv=float_mv * 2,
        change_pct=10.0,
        price=12.0,
        amount=10.0,
        turnover_rate=5.0,
        limit_times=0,
        limit_stat=f"{continuous}/{continuous}",
        industry="测试行业",
    )


class TestDragonStock:
    """测试龙头股数据类"""

    def test_to_dict(self):
        """测试转换为字典"""
        stock = DragonStock(
            code="000001",
            name="平安银行",
            stock_type="龙头",
            continuous=5,
            first_limit_time="09:35:00",
            float_mv=100.0,
            change_pct=10.0,
            reason="5板，09:35:00封板，流通市值100.00亿",
        )

        result = stock.to_dict()

        assert result["code"] == "000001"
        assert result["name"] == "平安银行"
        assert result["stock_type"] == "龙头"
        assert result["continuous"] == 5
        assert result["first_limit_time"] == "09:35:00"
        assert result["float_mv"] == 100.0
        assert result["change_pct"] == 10.0


class TestDragonHeadResult:
    """测试龙头识别结果数据类"""

    def test_to_dict(self):
        """测试转换为字典"""
        result = DragonHeadResult(
            date="2026-03-11",
            board_name="人工智能",
            dragon_head=DragonStock(
                code="000001",
                name="平安银行",
                stock_type="龙头",
                continuous=5,
                first_limit_time="09:35:00",
                float_mv=100.0,
                change_pct=10.0,
                reason="5板，09:35:00封板",
            ),
            followers=[
                DragonStock(
                    code="000002",
                    name="万科A",
                    stock_type="跟风",
                    continuous=2,
                    first_limit_time="11:00:00",
                    float_mv=80.0,
                    change_pct=10.0,
                    reason="2板，11:00:00封板",
                ),
            ],
            laggards=[],
            total_limit_up=2,
        )

        data = result.to_dict()

        assert data["date"] == "2026-03-11"
        assert data["board_name"] == "人工智能"
        assert data["dragon_head"]["code"] == "000001"
        assert len(data["followers"]) == 1
        assert len(data["laggards"]) == 0
        assert data["total_limit_up"] == 2


class TestDragonHeadProcessor:
    """测试龙头识别处理器"""

    @pytest.fixture
    def processor(self):
        """创建处理器实例"""
        return DragonHeadProcessor("人工智能", "2026-03-11")

    def test_match_board_limit_up_with_cons(self, processor):
        """测试匹配板块内涨停股：有成分股"""
        concept_cons = {"000001", "000002", "000003"}
        limit_up_items = [
            create_limit_up_item("000001", "平安银行"),
            create_limit_up_item("000004", "其他股票"),
        ]

        result = processor._match_board_limit_up(concept_cons, limit_up_items)

        assert len(result) == 1
        assert result[0].code == "000001"

    def test_match_board_limit_up_without_cons(self, processor):
        """测试匹配板块内涨停股：无成分股数据"""
        concept_cons = set()
        limit_up_items = [create_limit_up_item("000001", "平安银行")]

        result = processor._match_board_limit_up(concept_cons, limit_up_items)

        # 没有成分股数据时，返回所有涨停股
        assert len(result) == 1

    def test_identify_dragon_empty(self, processor):
        """测试识别龙头：空列表"""
        result = processor._identify_dragon([])

        assert result.date == "2026-03-11"
        assert result.board_name == "人工智能"
        assert result.dragon_head is None
        assert len(result.followers) == 0
        assert len(result.laggards) == 0
        assert result.total_limit_up == 0

    def test_identify_dragon_single(self, processor):
        """测试识别龙头：单只股票"""
        items = [create_limit_up_item("000001", "平安银行", continuous=3)]

        result = processor._identify_dragon(items)

        assert result.dragon_head is not None
        assert result.dragon_head.code == "000001"
        assert result.dragon_head.stock_type == "龙头"
        assert result.dragon_head.continuous == 3
        assert len(result.followers) == 0
        assert len(result.laggards) == 0
        assert result.total_limit_up == 1

    def test_identify_dragon_with_followers(self, processor):
        """测试识别龙头：有跟风股（10:30后封板）"""
        items = [
            create_limit_up_item("000001", "平安银行", continuous=5),
            create_limit_up_item("000002", "万科A", continuous=2, first_limit_time="11:00:00"),
        ]

        result = processor._identify_dragon(items)

        assert result.dragon_head.code == "000001"
        assert len(result.followers) == 1
        assert result.followers[0].code == "000002"
        assert result.followers[0].stock_type == "跟风"

    def test_identify_dragon_with_laggards(self, processor):
        """测试识别龙头：有补涨股（10:30前封板但非龙头）"""
        items = [
            create_limit_up_item("000001", "平安银行", continuous=5),
            create_limit_up_item("000002", "万科A", continuous=3, first_limit_time="10:15:00"),
        ]

        result = processor._identify_dragon(items)

        assert result.dragon_head.code == "000001"
        assert len(result.laggards) == 1
        assert result.laggards[0].code == "000002"
        assert result.laggards[0].stock_type == "补涨"

    def test_identify_dragon_sorting(self, processor):
        """测试识别龙头：排序逻辑"""
        items = [
            create_limit_up_item("000003", "股票C", continuous=2, first_limit_time="10:00:00"),
            create_limit_up_item("000001", "股票A", continuous=5),
            create_limit_up_item("000002", "股票B", continuous=3, first_limit_time="09:40:00"),
        ]

        result = processor._identify_dragon(items)

        # 龙头应该是连板数最高的 000001
        assert result.dragon_head.code == "000001"
        assert result.dragon_head.continuous == 5

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    @patch("openclaw_alpha.skills.theme_speculation.dragon_head_processor.dragon_head_processor.fetch_limit_up")
    @patch("openclaw_alpha.skills.theme_speculation.dragon_head_processor.dragon_head_processor.fetch_concept")
    async def test_analyze(self, mock_fetch_concept, mock_fetch_limit_up, processor):
        """测试完整分析流程"""
        from openclaw_alpha.skills.limit_up_tracker.limit_up_fetcher.models import (
            LimitUpResult,
        )

        # Mock 概念板块数据
        mock_fetch_concept.return_value = [
            {"code": "001", "name": "人工智能"},
        ]

        # Mock 涨停数据
        limit_up_result = LimitUpResult(
            date="2026-03-11",
            limit_type=LimitUpType.LIMIT_UP,
            total=2,
            continuous_stat={},
            items=[
                create_limit_up_item("000001", "平安银行", continuous=5),
                create_limit_up_item("000002", "万科A", continuous=2, first_limit_time="11:00:00"),
            ],
        )

        mock_fetch_limit_up.return_value = limit_up_result

        result = await processor.analyze()

        assert result.date == "2026-03-11"
        assert result.board_name == "人工智能"
        assert result.dragon_head is not None
        assert result.total_limit_up > 0
