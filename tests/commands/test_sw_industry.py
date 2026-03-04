# -*- coding: utf-8 -*-
"""申万行业指数行情查询测试"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from openclaw_alpha.commands.sw_industry import get_sw_industry_data


@pytest.fixture
def mock_sw_daily_df() -> pd.DataFrame:
    """构造模拟的申万行业指数 DataFrame"""
    return pd.DataFrame(
        {
            "ts_code": ["850531.SI", "851091.SI", "801030.SI"],
            "name": ["黄金", "锂电池", "钢铁"],
            "pct_change": [5.23, 3.45, 2.15],
            "close": [3256.78, 2156.34, 1567.89],
            "vol": [1234500, 987600, 654300],  # 手
            "amount": [4567000, 3218000, 1987000],  # 千元
            "float_mv": [10000000, 8000000, 5000000],  # 万元
            "total_mv": [20000000, 16000000, 10000000],  # 万元
            "pe": [25.6, 18.3, 12.5],
            "pb": [3.2, 2.5, 1.8],
        }
    )


@pytest.fixture
def mock_l1_df() -> pd.DataFrame:
    """构造模拟的一级行业 DataFrame"""
    return pd.DataFrame(
        {
            "ts_code": ["801030.SI", "801040.SI"],
            "name": ["钢铁", "有色金属"],
            "pct_change": [2.15, 3.52],
            "close": [1567.89, 2345.67],
            "vol": [654300, 789400],
            "amount": [1987000, 2568000],  # 千元
            "float_mv": [5000000, 6000000],  # 万元
            "total_mv": [10000000, 12000000],  # 万元
            "pe": [12.5, 15.8],
            "pb": [1.8, 2.2],
        }
    )


class TestGetSwIndustryData:
    """get_sw_industry_data 函数测试"""

    def test_token_not_configured(self) -> None:
        """测试 TOKEN 未配置"""
        with patch.dict("os.environ", {}, clear=True):
            result = get_sw_industry_data()

        assert result["success"] is False
        assert "TUSHARE_TOKEN" in result["error"]

    def test_success(self, mock_sw_daily_df: pd.DataFrame) -> None:
        """测试成功获取申万行业指数数据"""
        mock_pro = MagicMock()
        mock_pro.sw_daily.return_value = mock_sw_daily_df

        with patch.dict(
            "os.environ", {"TUSHARE_TOKEN": "test_token"}, clear=True
        ):
            with patch(
                "openclaw_alpha.commands.sw_industry.ts.pro_api",
                return_value=mock_pro,
            ):
                result = get_sw_industry_data(level="L3", top=50, sort_by="change_pct")

        assert result["success"] is True
        assert "timestamp" in result
        assert result["level"] == "L3"
        # L3 筛选只保留以 85 开头的代码，测试数据中有 2 个
        assert result["count"] == 2
        assert result["data_source"] == "Tushare"
        assert len(result["data"]) == 2

    def test_top_parameter(self, mock_sw_daily_df: pd.DataFrame) -> None:
        """测试 top 参数限制返回数量"""
        mock_pro = MagicMock()
        mock_pro.sw_daily.return_value = mock_sw_daily_df

        with patch.dict(
            "os.environ", {"TUSHARE_TOKEN": "test_token"}, clear=True
        ):
            with patch(
                "openclaw_alpha.commands.sw_industry.ts.pro_api",
                return_value=mock_pro,
            ):
                result = get_sw_industry_data(level="L3", top=2, sort_by="change_pct")

        assert result["count"] == 2
        assert len(result["data"]) == 2

    def test_sort_by_change_pct(self, mock_sw_daily_df: pd.DataFrame) -> None:
        """测试按涨跌幅排序"""
        mock_pro = MagicMock()
        mock_pro.sw_daily.return_value = mock_sw_daily_df

        with patch.dict(
            "os.environ", {"TUSHARE_TOKEN": "test_token"}, clear=True
        ):
            with patch(
                "openclaw_alpha.commands.sw_industry.ts.pro_api",
                return_value=mock_pro,
            ):
                result = get_sw_industry_data(level="L3", top=50, sort_by="change_pct")

        assert result["data"][0]["board_name"] == "黄金"
        assert result["data"][0]["change_pct"] == 5.23

    def test_sort_by_amount(self, mock_sw_daily_df: pd.DataFrame) -> None:
        """测试按成交额排序"""
        mock_pro = MagicMock()
        mock_pro.sw_daily.return_value = mock_sw_daily_df

        with patch.dict(
            "os.environ", {"TUSHARE_TOKEN": "test_token"}, clear=True
        ):
            with patch(
                "openclaw_alpha.commands.sw_industry.ts.pro_api",
                return_value=mock_pro,
            ):
                result = get_sw_industry_data(level="L3", top=50, sort_by="amount")

        assert result["data"][0]["board_name"] == "黄金"

    def test_level_l1_filter(self, mock_l1_df: pd.DataFrame) -> None:
        """测试一级行业筛选"""
        mock_pro = MagicMock()
        mock_pro.sw_daily.return_value = mock_l1_df

        with patch.dict(
            "os.environ", {"TUSHARE_TOKEN": "test_token"}, clear=True
        ):
            with patch(
                "openclaw_alpha.commands.sw_industry.ts.pro_api",
                return_value=mock_pro,
            ):
                result = get_sw_industry_data(level="L1", top=50, sort_by="change_pct")

        assert result["level"] == "L1"
        # L1 筛选后应该只剩以 801 开头的代码
        for item in result["data"]:
            assert item["board_code"].startswith("801")

    def test_date_parameter(self, mock_sw_daily_df: pd.DataFrame) -> None:
        """测试日期参数"""
        mock_pro = MagicMock()
        mock_pro.sw_daily.return_value = mock_sw_daily_df

        with patch.dict(
            "os.environ", {"TUSHARE_TOKEN": "test_token"}, clear=True
        ):
            with patch(
                "openclaw_alpha.commands.sw_industry.ts.pro_api",
                return_value=mock_pro,
            ):
                result = get_sw_industry_data(
                    trade_date="20260228", level="L3", top=50, sort_by="change_pct"
                )

        assert result["trade_date"] == "20260228"
        mock_pro.sw_daily.assert_called_once_with(trade_date="20260228")

    def test_data_fields(self, mock_sw_daily_df: pd.DataFrame) -> None:
        """测试返回数据包含必需字段"""
        mock_pro = MagicMock()
        mock_pro.sw_daily.return_value = mock_sw_daily_df

        with patch.dict(
            "os.environ", {"TUSHARE_TOKEN": "test_token"}, clear=True
        ):
            with patch(
                "openclaw_alpha.commands.sw_industry.ts.pro_api",
                return_value=mock_pro,
            ):
                result = get_sw_industry_data(level="L3", top=50, sort_by="change_pct")

        item = result["data"][0]
        required_fields = [
            "rank",
            "board_code",
            "board_name",
            "change_pct",
            "close",
            "volume",
            "amount",
            "turnover_rate",
            "pe",
            "pb",
        ]
        for field in required_fields:
            assert field in item, f"缺少必需字段: {field}"

    def test_field_conversion(self, mock_sw_daily_df: pd.DataFrame) -> None:
        """测试字段转换逻辑"""
        mock_pro = MagicMock()
        mock_pro.sw_daily.return_value = mock_sw_daily_df

        with patch.dict(
            "os.environ", {"TUSHARE_TOKEN": "test_token"}, clear=True
        ):
            with patch(
                "openclaw_alpha.commands.sw_industry.ts.pro_api",
                return_value=mock_pro,
            ):
                result = get_sw_industry_data(level="L3", top=50, sort_by="change_pct")

        item = result["data"][0]
        # volume: 1234500 手 -> 123.45 万手
        assert item["volume"] == pytest.approx(123.45, rel=0.01)
        # amount: 4567000000 元 -> 45.67 亿
        assert item["amount"] == pytest.approx(45.67, rel=0.01)

    def test_empty_dataframe_non_trading_day(self) -> None:
        """测试非交易日返回空数据"""
        mock_pro = MagicMock()
        mock_pro.sw_daily.return_value = pd.DataFrame()

        with patch.dict(
            "os.environ", {"TUSHARE_TOKEN": "test_token"}, clear=True
        ):
            with patch(
                "openclaw_alpha.commands.sw_industry.ts.pro_api",
                return_value=mock_pro,
            ):
                result = get_sw_industry_data(level="L3", top=50, sort_by="change_pct")

        assert result["success"] is True
        assert result["count"] == 0
        assert result["data"] == []

    def test_none_dataframe(self) -> None:
        """测试 None 返回空数据"""
        mock_pro = MagicMock()
        mock_pro.sw_daily.return_value = None

        with patch.dict(
            "os.environ", {"TUSHARE_TOKEN": "test_token"}, clear=True
        ):
            with patch(
                "openclaw_alpha.commands.sw_industry.ts.pro_api",
                return_value=mock_pro,
            ):
                result = get_sw_industry_data(level="L3", top=50, sort_by="change_pct")

        assert result["success"] is True
        assert result["count"] == 0
        assert result["data"] == []

    def test_api_exception_with_insufficient_points(self) -> None:
        """测试积分不足异常"""
        mock_pro = MagicMock()
        mock_pro.sw_daily.side_effect = Exception("积分不足，需要 120 积分")

        with patch.dict(
            "os.environ", {"TUSHARE_TOKEN": "test_token"}, clear=True
        ):
            with patch(
                "openclaw_alpha.commands.sw_industry.ts.pro_api",
                return_value=mock_pro,
            ):
                result = get_sw_industry_data(level="L3", top=50, sort_by="change_pct")

        assert result["success"] is False
        assert "积分" in result["error"]

    def test_api_exception_general(self) -> None:
        """测试通用 API 异常"""
        mock_pro = MagicMock()
        mock_pro.sw_daily.side_effect = Exception("网络错误")

        with patch.dict(
            "os.environ", {"TUSHARE_TOKEN": "test_token"}, clear=True
        ):
            with patch(
                "openclaw_alpha.commands.sw_industry.ts.pro_api",
                return_value=mock_pro,
            ):
                result = get_sw_industry_data(level="L3", top=50, sort_by="change_pct")

        assert result["success"] is False
        assert "网络错误" in result["error"]
