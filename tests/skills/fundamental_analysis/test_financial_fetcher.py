# -*- coding: utf-8 -*-
"""FinancialFetcher 测试"""

import json
from pathlib import Path

import pandas as pd
import pytest

from openclaw_alpha.skills.fundamental_analysis.financial_fetcher.akshare import (
    FinancialFetcherAkshare,
)
from openclaw_alpha.skills.fundamental_analysis.financial_fetcher.models import FinancialData


class TestFinancialFetcherAkshareTransform:
    """测试 FinancialFetcherAkshare 的数据转换"""

    @pytest.fixture
    def fetcher(self):
        """创建 fetcher 实例"""
        return FinancialFetcherAkshare()

    @pytest.fixture
    def sample_df(self, fixtures_dir: Path):
        """加载 API 响应 fixture"""
        fixture_file = fixtures_dir / "financial_api_response.json"
        with open(fixture_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return pd.DataFrame(data)

    def test_transform_basic(self, fetcher: FinancialFetcherAkshare, sample_df: pd.DataFrame):
        """测试基本转换"""
        result = fetcher._transform(sample_df, "000001")

        assert isinstance(result, FinancialData)
        assert result.code == "000001"
        assert result.name != ""
        assert result.report_date != ""

    def test_transform_fields(self, fetcher: FinancialFetcherAkshare, sample_df: pd.DataFrame):
        """测试字段映射"""
        result = fetcher._transform(sample_df, "000001")

        # 验证关键字段存在
        assert result.code == "000001"
        # ROE, EPS 等字段可能是 None（如果数据为空）
        # 但至少要有 code, name, report_date
        assert result.report_date is not None

    def test_transform_empty_df(self, fetcher: FinancialFetcherAkshare):
        """测试空 DataFrame 处理"""
        empty_df = pd.DataFrame()
        result = fetcher._transform(empty_df, "000001")

        assert result.code == "000001"
        assert result.name == ""
        assert result.report_date == ""

    def test_transform_nan_values(self, fetcher: FinancialFetcherAkshare):
        """测试 NaN 值处理"""
        # 构造包含 NaN 的数据
        data = {
            "SECURITY_NAME_ABBR": ["测试股票"],
            "REPORT_DATE": ["2025-09-30"],
            "ROEJQ": [float("nan")],
            "EPSJB": [None],
            "ZCFZL": [50.5],
        }
        df = pd.DataFrame(data)
        result = fetcher._transform(df, "000002")

        assert result.code == "000002"
        assert result.roe is None  # NaN 转为 None
        assert result.eps is None
        assert result.debt_ratio == 50.5

    def test_transform_date_format(self, fetcher: FinancialFetcherAkshare):
        """测试日期格式处理"""
        data = {
            "SECURITY_NAME_ABBR": ["测试股票"],
            "REPORT_DATE": ["2025-09-30 00:00:00"],
        }
        df = pd.DataFrame(data)
        result = fetcher._transform(df, "000003")

        # 日期应该只保留前 10 个字符
        assert result.report_date == "2025-09-30"


class TestFinancialData:
    """测试 FinancialData 模型"""

    def test_to_dict(self):
        """测试 to_dict 方法"""
        data = FinancialData(
            code="000001",
            name="平安银行",
            report_date="2025-09-30",
            roe=8.28,
            eps=1.87,
        )
        result = data.to_dict()

        assert result["code"] == "000001"
        assert result["name"] == "平安银行"
        assert result["roe"] == 8.28
        assert result["eps"] == 1.87

    def test_optional_fields(self):
        """测试可选字段默认为 None"""
        data = FinancialData(code="000001", name="测试", report_date="2025-09-30")

        assert data.roe is None
        assert data.eps is None
        assert data.debt_ratio is None
