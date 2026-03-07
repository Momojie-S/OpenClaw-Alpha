# -*- coding: utf-8 -*-
"""ForecastFetcher 测试"""

import pytest

from skills.risk_alert.scripts.forecast_fetcher.akshare import ForecastFetcherAkshare


class TestForecastFetcherAkshare:
    """ForecastFetcher AKShare 实现测试"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_transform(self, forecast_response):
        """测试数据转换"""
        fetcher = ForecastFetcherAkshare()
        records = fetcher._transform(forecast_response)

        assert len(records) == 3

        # 检查第一条（预增，无风险）
        assert records[0]["code"] == "000001"
        assert records[0]["name"] == "平安银行"
        assert records[0]["forecast_type"] == "预增"
        assert records[0]["risk_level"] == "无"

        # 检查第二条（首亏，高风险）
        assert records[1]["code"] == "000002"
        assert records[1]["name"] == "万科A"
        assert records[1]["forecast_type"] == "首亏"
        assert records[1]["risk_level"] == "高"

        # 检查第三条（不确定，中风险）
        assert records[2]["code"] == "000003"
        assert records[2]["name"] == "测试股票"
        assert records[2]["forecast_type"] == "不确定"
        assert records[2]["risk_level"] == "中"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_risk_level_mapping(self, forecast_response):
        """测试风险等级映射"""
        fetcher = ForecastFetcherAkshare()
        records = fetcher._transform(forecast_response)

        # 检查所有风险等级
        risk_levels = [r["risk_level"] for r in records]
        assert "无" in risk_levels
        assert "高" in risk_levels
        assert "中" in risk_levels

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_filter_by_risk_type(self, forecast_response):
        """测试按风险类型筛选"""
        fetcher = ForecastFetcherAkshare()
        records = fetcher._transform(forecast_response)

        # 筛选高风险
        high_risk = [r for r in records if r["forecast_type"] in fetcher.HIGH_RISK_TYPES]
        assert len(high_risk) == 1
        assert high_risk[0]["code"] == "000002"

        # 筛选中风险
        medium_risk = [r for r in records if r["forecast_type"] in fetcher.MEDIUM_RISK_TYPES]
        assert len(medium_risk) == 1
        assert medium_risk[0]["code"] == "000003"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_is_available(self):
        """测试可用性检查"""
        fetcher = ForecastFetcherAkshare()
        is_available, error = fetcher.is_available()

        # AKShare 无需配置，应该总是可用
        assert is_available is True
        assert error is None
