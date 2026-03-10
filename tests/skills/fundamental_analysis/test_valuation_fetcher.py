# -*- coding: utf-8 -*-
"""ValuationFetcher 测试"""

import json
from pathlib import Path

import pandas as pd
import pytest

from openclaw_alpha.skills.fundamental_analysis.valuation_fetcher.akshare import (
    ValuationFetcherAkshare,
    INDICATOR_MAP,
)
from openclaw_alpha.skills.fundamental_analysis.valuation_fetcher.models import ValuationData


class TestValuationFetcherAkshareTransform:
    """测试 ValuationFetcherAkshare 的数据转换"""

    @pytest.fixture
    def fetcher(self):
        """创建 fetcher 实例"""
        return ValuationFetcherAkshare()

    @pytest.fixture
    def sample_df(self, fixtures_dir: Path):
        """加载 API 响应 fixture"""
        fixture_file = fixtures_dir / "valuation_api_response.json"
        with open(fixture_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return pd.DataFrame(data)

    def test_transform_basic(self, fetcher: ValuationFetcherAkshare, sample_df: pd.DataFrame):
        """测试基本转换"""
        result = fetcher._transform(sample_df)

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(item, ValuationData) for item in result)

    def test_transform_fields(self, fetcher: ValuationFetcherAkshare, sample_df: pd.DataFrame):
        """测试字段映射"""
        result = fetcher._transform(sample_df)

        # 验证第一条数据
        first = result[0]
        assert first.date is not None
        assert first.value is not None

    def test_transform_empty_df(self, fetcher: ValuationFetcherAkshare):
        """测试空 DataFrame 处理"""
        empty_df = pd.DataFrame()
        result = fetcher._transform(empty_df)

        assert result == []

    def test_transform_nan_values(self, fetcher: ValuationFetcherAkshare):
        """测试 NaN 值被跳过"""
        data = {
            "date": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "value": [10.5, float("nan"), 11.2],
        }
        df = pd.DataFrame(data)
        result = fetcher._transform(df)

        # NaN 应该被跳过
        assert len(result) == 2
        assert result[0].value == 10.5
        assert result[1].value == 11.2


class TestIndicatorMap:
    """测试指标映射"""

    def test_indicator_map_exists(self):
        """测试指标映射定义正确"""
        assert "pe_ttm" in INDICATOR_MAP
        assert "pe_static" in INDICATOR_MAP
        assert "pb" in INDICATOR_MAP
        assert "market_cap" in INDICATOR_MAP
        assert "pcf" in INDICATOR_MAP

    def test_indicator_map_values(self):
        """测试指标映射值正确"""
        assert INDICATOR_MAP["pe_ttm"] == "市盈率(TTM)"
        assert INDICATOR_MAP["pb"] == "市净率"


class TestValuationData:
    """测试 ValuationData 模型"""

    def test_to_dict(self):
        """测试 to_dict 方法"""
        data = ValuationData(date="2025-03-07", value=4.87)
        result = data.to_dict()

        assert result["date"] == "2025-03-07"
        assert result["value"] == 4.87

    def test_optional_value(self):
        """测试 value 默认为 None"""
        data = ValuationData(date="2025-03-07")

        assert data.value is None
