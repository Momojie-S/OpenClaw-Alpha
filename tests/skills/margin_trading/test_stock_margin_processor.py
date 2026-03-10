# -*- coding: utf-8 -*-
"""个股融资融券 Processor 测试"""

import pytest
import pandas as pd

from openclaw_alpha.skills.margin_trading.stock_margin_processor.stock_margin_processor import (
    normalize_df,
    merge_stocks,
    process,
    format_text,
)


class TestNormalizeDf:
    """测试 normalize_df 函数"""

    def test_empty_df(self):
        """测试空数据框"""
        df = pd.DataFrame()
        mapping = {"标的证券代码": "code"}
        result = normalize_df(df, mapping)
        assert result.empty

    def test_normalize_sh_data(self):
        """测试沪市数据标准化"""
        df = pd.DataFrame({
            "标的证券代码": ["600000", "600001"],
            "标的证券简称": ["浦发银行", "邯郸钢铁"],
            "融资余额": [100000000, 50000000],
            "融资买入额": [10000000, 5000000],
            "融券余量": [100000, 50000],
            "融券卖出量": [10000, 5000],
        })
        mapping = {
            "标的证券代码": "code",
            "标的证券简称": "name",
            "融资余额": "financing_balance",
            "融资买入额": "financing_buy",
            "融券余量": "securities_balance",
            "融券卖出量": "securities_sell",
        }
        result = normalize_df(df, mapping)

        assert len(result) == 2
        assert "code" in result.columns
        assert "name" in result.columns
        assert result.iloc[0]["code"] == "600000"

    def test_normalize_partial_columns(self):
        """测试部分列缺失"""
        df = pd.DataFrame({
            "标的证券代码": ["600000"],
            "标的证券简称": ["浦发银行"],
        })
        mapping = {
            "标的证券代码": "code",
            "标的证券简称": "name",
        }
        result = normalize_df(df, mapping)

        assert len(result) == 1
        assert "code" in result.columns
        assert "name" in result.columns


class TestMergeStocks:
    """测试 merge_stocks 函数"""

    def test_merge_both_empty(self):
        """测试两个空数据框"""
        sh_df = pd.DataFrame()
        sz_df = pd.DataFrame()
        result = merge_stocks(sh_df, sz_df)
        assert result.empty

    def test_merge_sh_only(self):
        """测试只有沪市数据"""
        sh_df = pd.DataFrame({
            "标的证券代码": ["600000"],
            "标的证券简称": ["浦发银行"],
            "融资余额": [100000000],
            "融资买入额": [10000000],
            "融券余量": [100000],
            "融券卖出量": [10000],
        })
        sz_df = pd.DataFrame()
        result = merge_stocks(sh_df, sz_df)

        assert len(result) == 1
        assert result.iloc[0]["code"] == "600000"

    def test_merge_sz_only(self):
        """测试只有深市数据"""
        sh_df = pd.DataFrame()
        sz_df = pd.DataFrame({
            "证券代码": ["000001"],
            "证券简称": ["平安银行"],
            "融资余额": [50000000],
            "融资买入额": [5000000],
            "融券余量": [50000],
            "融券卖出量": [5000],
        })
        result = merge_stocks(sh_df, sz_df)

        assert len(result) == 1
        assert result.iloc[0]["code"] == "000001"

    def test_merge_both(self):
        """测试合并沪深数据"""
        sh_df = pd.DataFrame({
            "标的证券代码": ["600000"],
            "标的证券简称": ["浦发银行"],
            "融资余额": [100000000],
            "融资买入额": [10000000],
            "融券余量": [100000],
            "融券卖出量": [10000],
        })
        sz_df = pd.DataFrame({
            "证券代码": ["000001"],
            "证券简称": ["平安银行"],
            "融资余额": [50000000],
            "融资买入额": [5000000],
            "融券余量": [50000],
            "融券卖出量": [5000],
        })
        result = merge_stocks(sh_df, sz_df)

        assert len(result) == 2


class TestFormatText:
    """测试 format_text 函数"""

    def test_format_financing_empty(self):
        """测试空数据格式化（融资）"""
        data = {
            "date": "2026-03-08",
            "type": "financing",
            "stocks": [],
        }
        result = format_text(data)
        assert "2026-03-08" in result
        # 空列表时仍输出标题行
        assert "融资余额" in result

    def test_format_financing_with_data(self):
        """测试有数据格式化（融资）"""
        data = {
            "date": "2026-03-08",
            "type": "financing",
            "stocks": [
                {
                    "code": "600000",
                    "name": "浦发银行",
                    "financing_balance": 10.5,
                    "financing_buy": 1.2,
                },
            ],
        }
        result = format_text(data)
        assert "融资余额" in result
        assert "600000" in result
        assert "浦发银行" in result

    def test_format_securities_with_data(self):
        """测试有数据格式化（融券）"""
        data = {
            "date": "2026-03-08",
            "type": "securities",
            "stocks": [
                {
                    "code": "600000",
                    "name": "浦发银行",
                    "securities_balance": 100000,
                    "securities_sell": 10000,
                },
            ],
        }
        result = format_text(data)
        assert "融券余量" in result
        assert "600000" in result


class TestProcess:
    """测试 process 函数"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_process_no_data(self, monkeypatch):
        """测试无数据情况"""
        import openclaw_alpha.skills.margin_trading.stock_margin_processor.stock_margin_processor as module

        # Mock API 返回空数据
        monkeypatch.setattr(module, "get_sh_stocks", lambda x: pd.DataFrame())
        monkeypatch.setattr(module, "get_sz_stocks", lambda x: pd.DataFrame())

        result = process(date="2026-03-08", output="json")

        assert result["date"] == "2026-03-08"
        assert result["stocks"] == []
