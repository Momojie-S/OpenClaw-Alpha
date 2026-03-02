# -*- coding: utf-8 -*-
"""概念板块行情查询测试"""

from unittest.mock import patch

import pandas as pd
import pytest

from openclaw_alpha.commands.board_concept import get_concept_board_data


@pytest.fixture
def mock_concept_board_df() -> pd.DataFrame:
    """构造模拟的概念板块 DataFrame"""
    return pd.DataFrame(
        {
            "板块代码": ["BK0891", "BK0892", "BK0893"],
            "板块名称": ["人工智能", "新能源车", "芯片"],
            "最新价": [1250.5, 980.3, 760.2],
            "涨跌幅": [3.52, 2.15, 1.88],
            "涨跌额": [42.5, 20.8, 14.2],
            "上涨家数": [45, 32, 28],
            "下跌家数": [5, 8, 12],
            "领涨股票": ["科大讯飞", "比亚迪", "中芯国际"],
            "领涨股票_涨跌幅": [5.23, 4.12, 3.56],
            "总成交量": [125.6, 98.3, 76.2],
            "总成交额": [250.5, 180.2, 120.8],
            "换手率": [3.21, 2.56, 1.89],
            "总市值": [890.5, 650.2, 420.8],
        }
    )


class TestGetConceptBoardData:
    """get_concept_board_data 函数测试"""

    def test_success(self, mock_concept_board_df: pd.DataFrame) -> None:
        """测试成功获取概念板块数据"""
        with patch(
            "openclaw_alpha.commands.board_concept.ak.stock_board_concept_name_em",
            return_value=mock_concept_board_df,
        ):
            result = get_concept_board_data(top=20, sort_by="change_pct")

        assert result["success"] is True
        assert "timestamp" in result
        assert "trade_date" in result
        assert result["count"] == 3
        assert len(result["data"]) == 3
        assert result["data_source"] == "东方财富"

    def test_top_parameter(self, mock_concept_board_df: pd.DataFrame) -> None:
        """测试 top 参数限制返回数量"""
        with patch(
            "openclaw_alpha.commands.board_concept.ak.stock_board_concept_name_em",
            return_value=mock_concept_board_df,
        ):
            result = get_concept_board_data(top=2, sort_by="change_pct")

        assert result["count"] == 2
        assert len(result["data"]) == 2

    def test_sort_by_change_pct(self, mock_concept_board_df: pd.DataFrame) -> None:
        """测试按涨跌幅排序"""
        with patch(
            "openclaw_alpha.commands.board_concept.ak.stock_board_concept_name_em",
            return_value=mock_concept_board_df,
        ):
            result = get_concept_board_data(top=20, sort_by="change_pct")

        assert result["data"][0]["board_name"] == "人工智能"
        assert result["data"][0]["change_pct"] == 3.52

    def test_sort_by_amount(self, mock_concept_board_df: pd.DataFrame) -> None:
        """测试按成交额排序"""
        with patch(
            "openclaw_alpha.commands.board_concept.ak.stock_board_concept_name_em",
            return_value=mock_concept_board_df,
        ):
            result = get_concept_board_data(top=20, sort_by="amount")

        assert result["data"][0]["board_name"] == "人工智能"
        assert result["data"][0]["amount"] == 250.5

    def test_data_fields(self, mock_concept_board_df: pd.DataFrame) -> None:
        """测试返回数据包含必需字段"""
        with patch(
            "openclaw_alpha.commands.board_concept.ak.stock_board_concept_name_em",
            return_value=mock_concept_board_df,
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

    def test_empty_dataframe(self) -> None:
        """测试空 DataFrame 返回失败"""
        with patch(
            "openclaw_alpha.commands.board_concept.ak.stock_board_concept_name_em",
            return_value=pd.DataFrame(),
        ):
            result = get_concept_board_data(top=20, sort_by="change_pct")

        assert result["success"] is False
        assert "error" in result

    def test_none_dataframe(self) -> None:
        """测试 None 返回失败"""
        with patch(
            "openclaw_alpha.commands.board_concept.ak.stock_board_concept_name_em",
            return_value=None,
        ):
            result = get_concept_board_data(top=20, sort_by="change_pct")

        assert result["success"] is False
        assert "error" in result

    def test_exception_handling(self) -> None:
        """测试异常处理"""
        with patch(
            "openclaw_alpha.commands.board_concept.ak.stock_board_concept_name_em",
            side_effect=Exception("网络错误"),
        ):
            result = get_concept_board_data(top=20, sort_by="change_pct")

        assert result["success"] is False
        assert "网络错误" in result["error"]
