# -*- coding: utf-8 -*-
"""涨停追踪 Fetcher 测试"""

import pytest
import pandas as pd
from unittest.mock import AsyncMock, patch

from openclaw_alpha.skills.limit_up_tracker.limit_up_fetcher.models import (
    LimitUpItem,
    LimitUpResult,
    LimitUpType,
)
from openclaw_alpha.skills.limit_up_tracker.limit_up_fetcher.akshare import LimitUpFetcherAkshare
from openclaw_alpha.skills.limit_up_tracker.limit_up_fetcher.limit_up_fetcher import (
    LimitUpFetcher,
    format_output,
)


class TestLimitUpFetcherAkshareTransform:
    """LimitUpFetcherAkshare 转换逻辑测试"""

    @pytest.fixture
    def fetcher(self):
        return LimitUpFetcherAkshare()

    # ============== 涨停股转换测试 ==============

    def test_transform_limit_up_basic(self, fetcher):
        """基本涨停股转换"""
        df = pd.DataFrame([
            {
                "代码": "000001",
                "名称": "平安银行",
                "涨跌幅": 10.0,
                "最新价": 15.0,
                "成交额": 1000000000,
                "流通市值": 20000000000,
                "总市值": 30000000000,
                "换手率": 5.0,
                "首次封板时间": "09:30:00",
                "最后封板时间": "14:50:00",
                "炸板次数": 0,
                "涨停统计": "3/5",
                "连板数": 3,
                "所属行业": "银行",
            }
        ])

        items = fetcher._transform(df, LimitUpType.LIMIT_UP)

        assert len(items) == 1
        item = items[0]
        assert item.code == "000001"
        assert item.name == "平安银行"
        assert item.change_pct == 10.0
        assert item.price == 15.0
        assert item.amount == 10.0  # 10亿
        assert item.float_mv == 200.0  # 200亿
        assert item.total_mv == 300.0  # 300亿
        assert item.turnover_rate == 5.0
        assert item.first_limit_time == "09:30:00"
        assert item.last_limit_time == "14:50:00"
        assert item.limit_times == 0
        assert item.limit_stat == "3/5"
        assert item.continuous == 3
        assert item.industry == "银行"

    def test_transform_limit_up_multiple_items(self, fetcher):
        """多只涨停股转换"""
        df = pd.DataFrame([
            {
                "代码": "000001",
                "名称": "平安银行",
                "涨跌幅": 10.0,
                "最新价": 15.0,
                "成交额": 1000000000,
                "流通市值": 20000000000,
                "总市值": 30000000000,
                "换手率": 5.0,
                "首次封板时间": "09:30:00",
                "最后封板时间": "14:50:00",
                "炸板次数": 0,
                "涨停统计": "1/1",
                "连板数": 1,
                "所属行业": "银行",
            },
            {
                "代码": "000002",
                "名称": "万科A",
                "涨跌幅": 9.98,
                "最新价": 20.0,
                "成交额": 2000000000,
                "流通市值": 25000000000,
                "总市值": 35000000000,
                "换手率": 8.0,
                "首次封板时间": "10:00:00",
                "最后封板时间": "14:00:00",
                "炸板次数": 2,
                "涨停统计": "2/3",
                "连板数": 2,
                "所属行业": "房地产",
            },
        ])

        items = fetcher._transform(df, LimitUpType.LIMIT_UP)

        assert len(items) == 2
        assert items[0].code == "000001"
        assert items[1].code == "000002"
        assert items[1].continuous == 2

    def test_transform_limit_up_empty_df(self, fetcher):
        """空 DataFrame 转换"""
        df = pd.DataFrame()
        items = fetcher._transform(df, LimitUpType.LIMIT_UP)
        assert items == []

    # ============== 跌停股转换测试 ==============

    def test_transform_limit_down(self, fetcher):
        """跌停股转换"""
        df = pd.DataFrame([
            {
                "代码": "000001",
                "名称": "平安银行",
                "涨跌幅": -10.0,
                "最新价": 12.27,
                "成交额": 500000000,
                "流通市值": 20000000000,
                "总市值": 30000000000,
                "换手率": 2.5,
                "首次封板时间": "10:00:00",
                "最后封板时间": "14:00:00",
                "炸板次数": 1,
                "涨停统计": "",
                "连板数": 0,
                "所属行业": "银行",
            }
        ])

        items = fetcher._transform(df, LimitUpType.LIMIT_DOWN)

        assert len(items) == 1
        assert items[0].change_pct == -10.0
        assert items[0].continuous == 0  # 跌停无连板数

    # ============== 炸板股转换测试 ==============

    def test_transform_broken(self, fetcher):
        """炸板股转换"""
        df = pd.DataFrame([
            {
                "代码": "000001",
                "名称": "平安银行",
                "涨跌幅": 5.0,
                "最新价": 14.5,
                "成交额": 800000000,
                "流通市值": 20000000000,
                "总市值": 30000000000,
                "换手率": 4.0,
            }
        ])

        items = fetcher._transform(df, LimitUpType.BROKEN)

        assert len(items) == 1
        assert items[0].code == "000001"
        assert items[0].change_pct == 5.0
        assert items[0].first_limit_time == ""  # 炸板无封板时间
        assert items[0].continuous == 0

    # ============== 昨日涨停转换测试 ==============

    def test_transform_previous(self, fetcher):
        """昨日涨停转换"""
        df = pd.DataFrame([
            {
                "代码": "000001",
                "名称": "平安银行",
                "涨跌幅": 3.0,
                "最新价": 15.45,
                "成交额": 1200000000,
                "流通市值": 20000000000,
                "总市值": 30000000000,
                "换手率": 6.0,
                "昨日封板时间": "09:30:00",
                "涨停统计": "3/5",
                "昨日连板数": 2,
                "所属行业": "银行",
            }
        ])

        items = fetcher._transform(df, LimitUpType.PREVIOUS)

        assert len(items) == 1
        assert items[0].change_pct == 3.0
        assert items[0].first_limit_time == "09:30:00"
        assert items[0].continuous == 2
        assert items[0].limit_stat == "3/5"


class TestLimitUpFetcher:
    """LimitUpFetcher 入口类测试"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_continuous_stat_calculation(self):
        """连板统计计算"""
        fetcher = LimitUpFetcher()

        # Mock 返回数据
        mock_result = LimitUpResult(
            date="20260307",
            limit_type=LimitUpType.LIMIT_UP,
            items=[
                LimitUpItem(
                    code="000001", name="股票1", change_pct=10.0, price=10.0,
                    amount=1.0, float_mv=10.0, total_mv=20.0, turnover_rate=5.0,
                    first_limit_time="09:30", last_limit_time="14:00", limit_times=0,
                    limit_stat="", continuous=1, industry=""
                ),
                LimitUpItem(
                    code="000002", name="股票2", change_pct=10.0, price=10.0,
                    amount=1.0, float_mv=10.0, total_mv=20.0, turnover_rate=5.0,
                    first_limit_time="09:30", last_limit_time="14:00", limit_times=0,
                    limit_stat="", continuous=2, industry=""
                ),
                LimitUpItem(
                    code="000003", name="股票3", change_pct=10.0, price=10.0,
                    amount=1.0, float_mv=10.0, total_mv=20.0, turnover_rate=5.0,
                    first_limit_time="09:30", last_limit_time="14:00", limit_times=0,
                    limit_stat="", continuous=2, industry=""
                ),
                LimitUpItem(
                    code="000004", name="股票4", change_pct=10.0, price=10.0,
                    amount=1.0, float_mv=10.0, total_mv=20.0, turnover_rate=5.0,
                    first_limit_time="09:30", last_limit_time="14:00", limit_times=0,
                    limit_stat="", continuous=3, industry=""
                ),
                LimitUpItem(
                    code="000005", name="股票5", change_pct=10.0, price=10.0,
                    amount=1.0, float_mv=10.0, total_mv=20.0, turnover_rate=5.0,
                    first_limit_time="09:30", last_limit_time="14:00", limit_times=0,
                    limit_stat="", continuous=5, industry=""  # 5连板归为4+
                ),
            ],
            total=5,
            continuous_stat={},
        )

        # Mock _select_available 和 method.fetch
        with patch.object(fetcher, '_select_available') as mock_select:
            mock_method = AsyncMock()
            mock_method.fetch.return_value = mock_result
            mock_select.return_value = (mock_method, [])

            result = await fetcher.fetch("2026-03-07")

            # 检查连板统计
            assert result.continuous_stat[1] == 1  # 首板 1 只
            assert result.continuous_stat[2] == 2  # 2板 2 只
            assert result.continuous_stat[3] == 1  # 3板 1 只
            assert result.continuous_stat[4] == 1  # 4+板 1 只（5板归为4+）


class TestFormatOutput:
    """格式化输出测试"""

    def test_format_output_basic(self):
        """基本格式化"""
        result = LimitUpResult(
            date="20260307",
            limit_type=LimitUpType.LIMIT_UP,
            items=[
                LimitUpItem(
                    code="000001", name="平安银行", change_pct=10.0, price=15.0,
                    amount=10.0, float_mv=200.0, total_mv=300.0, turnover_rate=5.0,
                    first_limit_time="09:30:00", last_limit_time="14:50:00", limit_times=0,
                    limit_stat="1/1", continuous=1, industry="银行"
                ),
            ],
            total=1,
            continuous_stat={1: 1},
        )

        output = format_output(result)

        assert "涨停股池" in output
        assert "20260307" in output
        assert "共 1 只" in output
        assert "连板统计" in output
        assert "000001" in output
        assert "平安银行" in output

    def test_format_output_min_continuous(self):
        """最小连板数筛选"""
        result = LimitUpResult(
            date="20260307",
            limit_type=LimitUpType.LIMIT_UP,
            items=[
                LimitUpItem(
                    code="000001", name="首板", change_pct=10.0, price=10.0,
                    amount=1.0, float_mv=10.0, total_mv=20.0, turnover_rate=5.0,
                    first_limit_time="", last_limit_time="", limit_times=0,
                    limit_stat="", continuous=1, industry=""
                ),
                LimitUpItem(
                    code="000002", name="二板", change_pct=10.0, price=10.0,
                    amount=1.0, float_mv=10.0, total_mv=20.0, turnover_rate=5.0,
                    first_limit_time="", last_limit_time="", limit_times=0,
                    limit_stat="", continuous=2, industry=""
                ),
            ],
            total=2,
            continuous_stat={1: 1, 2: 1},
        )

        # 只显示2板以上
        output = format_output(result, min_continuous=2)

        assert "000002" in output
        assert "000001" not in output  # 被筛选掉

    def test_format_output_top_n(self):
        """Top N 限制"""
        items = [
            LimitUpItem(
                code=f"00000{i}", name=f"股票{i}", change_pct=10.0, price=10.0,
                amount=1.0, float_mv=10.0, total_mv=20.0, turnover_rate=5.0,
                first_limit_time="", last_limit_time="", limit_times=0,
                limit_stat="", continuous=i, industry=""
            )
            for i in range(1, 6)
        ]

        result = LimitUpResult(
            date="20260307",
            limit_type=LimitUpType.LIMIT_UP,
            items=items,
            total=5,
            continuous_stat={1: 1, 2: 1, 3: 1, 4: 1, 5: 1},
        )

        output = format_output(result, top_n=3)

        # 只显示3条
        assert "000005" in output  # 5板
        assert "000004" in output  # 4板
        assert "000003" in output  # 3板
        # 2板和1板不在Top 3

    def test_format_output_empty(self):
        """空数据格式化"""
        result = LimitUpResult(
            date="20260307",
            limit_type=LimitUpType.LIMIT_UP,
            items=[],
            total=0,
            continuous_stat={},
        )

        output = format_output(result)

        assert "共 0 只" in output
        assert "无符合条件的股票" in output

    def test_format_output_limit_down(self):
        """跌停格式化"""
        result = LimitUpResult(
            date="20260307",
            limit_type=LimitUpType.LIMIT_DOWN,
            items=[
                LimitUpItem(
                    code="000001", name="跌停股", change_pct=-10.0, price=10.0,
                    amount=1.0, float_mv=10.0, total_mv=20.0, turnover_rate=5.0,
                    first_limit_time="", last_limit_time="", limit_times=0,
                    limit_stat="", continuous=0, industry=""
                ),
            ],
            total=1,
            continuous_stat={},
        )

        output = format_output(result)

        assert "跌停股池" in output

    def test_format_output_broken(self):
        """炸板格式化"""
        result = LimitUpResult(
            date="20260307",
            limit_type=LimitUpType.BROKEN,
            items=[
                LimitUpItem(
                    code="000001", name="炸板股", change_pct=5.0, price=10.0,
                    amount=1.0, float_mv=10.0, total_mv=20.0, turnover_rate=5.0,
                    first_limit_time="", last_limit_time="", limit_times=3,
                    limit_stat="", continuous=0, industry=""
                ),
            ],
            total=1,
            continuous_stat={},
        )

        output = format_output(result)

        assert "炸板股池" in output


class TestLimitUpModels:
    """数据类型测试"""

    def test_limit_up_item_to_dict(self):
        """LimitUpItem 序列化"""
        item = LimitUpItem(
            code="000001",
            name="平安银行",
            change_pct=10.0,
            price=15.0,
            amount=10.0,
            float_mv=200.0,
            total_mv=300.0,
            turnover_rate=5.0,
            first_limit_time="09:30:00",
            last_limit_time="14:50:00",
            limit_times=0,
            limit_stat="1/1",
            continuous=1,
            industry="银行",
        )

        d = item.to_dict()

        assert d["code"] == "000001"
        assert d["name"] == "平安银行"
        assert d["change_pct"] == 10.0
        assert d["continuous"] == 1

    def test_limit_up_result_to_dict(self):
        """LimitUpResult 序列化"""
        item = LimitUpItem(
            code="000001", name="平安银行", change_pct=10.0, price=15.0,
            amount=10.0, float_mv=200.0, total_mv=300.0, turnover_rate=5.0,
            first_limit_time="09:30:00", last_limit_time="14:50:00", limit_times=0,
            limit_stat="1/1", continuous=1, industry="银行"
        )

        result = LimitUpResult(
            date="20260307",
            limit_type=LimitUpType.LIMIT_UP,
            items=[item],
            total=1,
            continuous_stat={1: 1},
        )

        d = result.to_dict()

        assert d["date"] == "20260307"
        assert d["limit_type"] == "limit_up"
        assert d["total"] == 1
        assert len(d["items"]) == 1
        assert d["continuous_stat"] == {1: 1}

    def test_limit_up_type_enum(self):
        """LimitUpType 枚举"""
        assert LimitUpType.LIMIT_UP.value == "limit_up"
        assert LimitUpType.LIMIT_DOWN.value == "limit_down"
        assert LimitUpType.BROKEN.value == "broken"
        assert LimitUpType.PREVIOUS.value == "previous"
