# -*- coding: utf-8 -*-
"""IndustryInfoFetcher 测试"""

import pytest

from openclaw_alpha.skills.portfolio_analysis.industry_fetcher.industry_fetcher import (
    IndustryInfo,
    IndustryInfoFetcher,
)
from openclaw_alpha.skills.portfolio_analysis.industry_fetcher.akshare import (
    IndustryInfoFetcherAkshare,
)


class TestIndustryInfo:
    """测试 IndustryInfo 数据类"""

    def test_create(self):
        """测试创建"""
        info = IndustryInfo(code="000001", name="平安银行", industry="银行")
        assert info.code == "000001"
        assert info.name == "平安银行"
        assert info.industry == "银行"


class TestIndustryInfoFetcherAkshareParse:
    """测试 AKShare 实现的解析逻辑"""

    def test_parse_info_valid(self):
        """测试有效数据解析"""
        import pandas as pd

        fetcher = IndustryInfoFetcherAkshare()

        # 模拟 API 返回的数据
        df = pd.DataFrame({
            "item": ["股票代码", "股票简称", "行业"],
            "value": ["000001", "平安银行", "银行"],
        })

        result = fetcher._parse_info(df, "000001")

        assert result is not None
        assert result.code == "000001"
        assert result.name == "平安银行"
        assert result.industry == "银行"

    def test_parse_info_empty(self):
        """测试空数据"""
        import pandas as pd

        fetcher = IndustryInfoFetcherAkshare()

        df = pd.DataFrame()
        result = fetcher._parse_info(df, "000001")

        assert result is None

    def test_parse_info_none(self):
        """测试 None 数据"""
        fetcher = IndustryInfoFetcherAkshare()

        result = fetcher._parse_info(None, "000001")

        assert result is None

    def test_parse_info_missing_fields(self):
        """测试缺失字段"""
        import pandas as pd

        fetcher = IndustryInfoFetcherAkshare()

        # 只有部分字段
        df = pd.DataFrame({
            "item": ["股票代码", "股票简称"],
            "value": ["000001", "平安银行"],
        })

        result = fetcher._parse_info(df, "000001")

        assert result is not None
        assert result.industry == "未知"  # 默认值


class TestIndustryInfoFetcherAkshareTransform:
    """测试 AKShare 实现的转换逻辑"""

    def test_transform_basic(self):
        """测试基本转换"""
        import pandas as pd

        fetcher = IndustryInfoFetcherAkshare()

        df = pd.DataFrame({
            "item": ["股票代码", "股票简称", "行业"],
            "value": ["000001", "平安银行", "银行"],
        })

        info = fetcher._parse_info(df, "000001")

        assert info.code == "000001"
        assert info.name == "平安银行"
        assert info.industry == "银行"
