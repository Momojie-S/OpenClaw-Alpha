# -*- coding: utf-8 -*-
"""限售解禁 Fetcher 测试"""

import pytest
import pandas as pd

from skills.restricted_release.scripts.restricted_release_fetcher.restricted_release_fetcher import (
    RestrictedReleaseFetcherAkshare,
)


class TestTransformDetail:
    """测试 _transform_detail 方法"""

    def test_empty_df(self):
        """测试空数据"""
        fetcher = RestrictedReleaseFetcherAkshare()
        df = pd.DataFrame()
        result = fetcher._transform_detail(df)
        assert result == []

    def test_transform_single_record(self):
        """测试单条记录转换"""
        fetcher = RestrictedReleaseFetcherAkshare()
        df = pd.DataFrame({
            "股票代码": ["600000"],
            "股票简称": ["浦发银行"],
            "解禁时间": ["2026-03-15"],
            "限售股类型": ["定向增发"],
            "解禁数量": [1000000],
            "实际解禁数量": [900000],
            "实际解禁市值": [5000000],
            "占解禁前流通市值比例": [0.15],
            "解禁前一交易日收盘价": [5.5],
        })

        result = fetcher._transform_detail(df)

        assert len(result) == 1
        assert result[0]["code"] == "600000"
        assert result[0]["name"] == "浦发银行"
        assert result[0]["release_date"] == "2026-03-15"
        assert result[0]["release_volume"] == 1000000
        assert result[0]["actual_release_value"] == 5000000

    def test_transform_multiple_records(self):
        """测试多条记录转换"""
        fetcher = RestrictedReleaseFetcherAkshare()
        df = pd.DataFrame({
            "股票代码": ["600000", "000001"],
            "股票简称": ["浦发银行", "平安银行"],
            "解禁时间": ["2026-03-15", "2026-03-16"],
            "限售股类型": ["定向增发", "股权激励"],
            "解禁数量": [1000000, 2000000],
            "实际解禁数量": [900000, 1800000],
            "实际解禁市值": [5000000, 10000000],
            "占解禁前流通市值比例": [0.15, 0.20],
            "解禁前一交易日收盘价": [5.5, 10.0],
        })

        result = fetcher._transform_detail(df)

        assert len(result) == 2
        assert result[0]["code"] == "600000"
        assert result[1]["code"] == "000001"

    def test_transform_with_none_values(self):
        """测试包含 None 值的记录"""
        fetcher = RestrictedReleaseFetcherAkshare()
        df = pd.DataFrame({
            "股票代码": ["600000"],
            "股票简称": ["浦发银行"],
            "解禁时间": ["2026-03-15"],
            "限售股类型": ["定向增发"],
            "解禁数量": [None],
            "实际解禁数量": [900000],
            "实际解禁市值": [5000000],
            "占解禁前流通市值比例": [0.15],
            "解禁前一交易日收盘价": [5.5],
        })

        result = fetcher._transform_detail(df)

        assert len(result) == 1
        assert result[0]["release_volume"] == 0  # None 转为 0


class TestTransformQueue:
    """测试 _transform_queue 方法"""

    def test_empty_df(self):
        """测试空数据"""
        fetcher = RestrictedReleaseFetcherAkshare()
        df = pd.DataFrame()
        result = fetcher._transform_queue(df)
        assert result == []

    def test_transform_queue_record(self):
        """测试解禁排期记录转换"""
        fetcher = RestrictedReleaseFetcherAkshare()
        df = pd.DataFrame({
            "解禁时间": ["2026-03-15"],
            "解禁股东数": [5],
            "解禁数量": [1000000],
            "实际解禁数量": [900000],
            "未解禁数量": [100000],
            "实际解禁数量市值": [5000000],
            "占总市值比例": [0.05],
            "占流通市值比例": [0.15],
            "解禁前一交易日收盘价": [5.5],
            "限售股类型": ["定向增发"],
        })

        result = fetcher._transform_queue(df)

        assert len(result) == 1
        assert result[0]["release_date"] == "2026-03-15"
        assert result[0]["shareholder_count"] == 5
        assert result[0]["unreleased_volume"] == 100000


class TestTransformSummary:
    """测试 _transform_summary 方法"""

    def test_empty_df(self):
        """测试空数据"""
        fetcher = RestrictedReleaseFetcherAkshare()
        df = pd.DataFrame()
        result = fetcher._transform_summary(df)
        assert result == []

    def test_transform_summary_record(self):
        """测试汇总记录转换"""
        fetcher = RestrictedReleaseFetcherAkshare()
        df = pd.DataFrame({
            "解禁时间": ["2026-03-15"],
            "当日解禁股票家数": [10],
            "解禁数量": [50000000],
            "实际解禁数量": [45000000],
            "实际解禁市值": [200000000],
        })

        result = fetcher._transform_summary(df)

        assert len(result) == 1
        assert result[0]["release_date"] == "2026-03-15"
        assert result[0]["stock_count"] == 10
        assert result[0]["release_volume"] == 50000000


class TestFetchMethod:
    """测试 FetchMethod 属性"""

    def test_method_attributes(self):
        """测试方法属性"""
        fetcher = RestrictedReleaseFetcherAkshare()

        assert fetcher.name == "restricted_release_akshare"
        assert fetcher.required_data_source == "akshare"
        assert fetcher.priority == 10

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_fetch_unknown_mode(self):
        """测试未知模式"""
        fetcher = RestrictedReleaseFetcherAkshare()
        result = await fetcher.fetch({"mode": "unknown"})

        assert result["mode"] == "unknown"
        assert result["data"] == []
        assert "error" in result["meta"]

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_fetch_queue_missing_symbol(self):
        """测试 queue 模式缺少股票代码"""
        fetcher = RestrictedReleaseFetcherAkshare()
        result = await fetcher.fetch({"mode": "queue"})

        assert result["mode"] == "queue"
        assert result["data"] == []
        assert "error" in result["meta"]
