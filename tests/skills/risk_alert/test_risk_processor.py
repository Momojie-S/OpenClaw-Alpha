# -*- coding: utf-8 -*-
"""RiskProcessor 测试"""

from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from openclaw_alpha.skills.risk_alert.risk_processor.risk_processor import RiskProcessor


class TestRiskProcessor:
    """RiskProcessor 测试"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_calculate_rating_high_risk(self):
        """测试高风险评级"""
        processor = RiskProcessor("000001")

        risks = [
            {"type": "业绩风险", "level": "高", "detail": "业绩首亏"},
            {"type": "价格风险", "level": "中", "detail": "连续下跌"},
        ]

        rating = processor._calculate_rating(risks)
        assert rating == "高"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_calculate_rating_medium_risk(self):
        """测试中风险评级"""
        processor = RiskProcessor("000001")

        risks = [
            {"type": "价格风险", "level": "中", "detail": "连续下跌"},
            {"type": "资金风险", "level": "低", "detail": "资金流出"},
        ]

        rating = processor._calculate_rating(risks)
        assert rating == "中"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_calculate_rating_low_risk(self):
        """测试低风险评级"""
        processor = RiskProcessor("000001")

        risks = [
            {"type": "资金风险", "level": "低", "detail": "资金流出"},
        ]

        rating = processor._calculate_rating(risks)
        assert rating == "低"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_calculate_rating_normal(self):
        """测试正常评级"""
        processor = RiskProcessor("000001")

        risks = []

        rating = processor._calculate_rating(risks)
        assert rating == "正常"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_generate_suggestions(self):
        """测试生成建议"""
        processor = RiskProcessor("000001")

        # 无风险
        suggestions = processor._generate_suggestions([])
        assert "暂无明显风险信号" in suggestions

        # 业绩风险
        risks = [{"type": "业绩风险", "level": "高", "detail": "业绩首亏"}]
        suggestions = processor._generate_suggestions(risks)
        assert "关注业绩公告详情" in suggestions

        # 价格风险
        risks = [{"type": "价格风险", "level": "中", "detail": "连续下跌"}]
        suggestions = processor._generate_suggestions(risks)
        assert "关注下跌原因" in " ".join(suggestions)  # 检查是否包含关键词

        # 资金风险
        risks = [{"type": "资金风险", "level": "中", "detail": "资金流出"}]
        suggestions = processor._generate_suggestions(risks)
        assert "关注主力资金动向" in suggestions

        # 多风险叠加
        risks = [
            {"type": "业绩风险", "level": "高", "detail": "业绩首亏"},
            {"type": "价格风险", "level": "中", "detail": "连续下跌"},
        ]
        suggestions = processor._generate_suggestions(risks)
        assert any("多风险叠加" in s for s in suggestions)  # 检查是否包含关键词

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_check_forecast_risk_high(self, forecast_response):
        """测试业绩风险检查 - 高风险"""
        processor = RiskProcessor("000002")

        with patch(
            "openclaw_alpha.skills.risk_alert.forecast_fetcher.fetch",
            new_callable=AsyncMock,
        ) as mock_fetch:
            # 模拟 fetch 返回数据
            from openclaw_alpha.skills.risk_alert.forecast_fetcher.akshare import ForecastFetcherAkshare

            fetcher = ForecastFetcherAkshare()
            mock_fetch.return_value = fetcher._transform(forecast_response)

            risk = await processor._check_forecast_risk()

            assert risk is not None
            assert risk["type"] == "业绩风险"
            assert risk["level"] == "高"
            assert "首亏" in risk["detail"]

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_check_forecast_risk_medium(self, forecast_response):
        """测试业绩风险检查 - 中风险"""
        processor = RiskProcessor("000003")

        with patch(
            "openclaw_alpha.skills.risk_alert.forecast_fetcher.fetch",
            new_callable=AsyncMock,
        ) as mock_fetch:
            from openclaw_alpha.skills.risk_alert.forecast_fetcher.akshare import ForecastFetcherAkshare

            fetcher = ForecastFetcherAkshare()
            mock_fetch.return_value = fetcher._transform(forecast_response)

            risk = await processor._check_forecast_risk()

            assert risk is not None
            assert risk["type"] == "业绩风险"
            assert risk["level"] == "中"
            assert "不确定" in risk["detail"]

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_check_forecast_risk_no_risk(self, forecast_response):
        """测试业绩风险检查 - 无风险"""
        processor = RiskProcessor("000001")

        with patch(
            "openclaw_alpha.skills.risk_alert.forecast_fetcher.fetch",
            new_callable=AsyncMock,
        ) as mock_fetch:
            from openclaw_alpha.skills.risk_alert.forecast_fetcher.akshare import ForecastFetcherAkshare

            fetcher = ForecastFetcherAkshare()
            mock_fetch.return_value = fetcher._transform(forecast_response)

            risk = await processor._check_forecast_risk()

            # 预增是低风险，不触发风险
            assert risk is None

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_check_price_risk_high(self):
        """测试价格风险检查 - 高风险"""
        processor = RiskProcessor("000001")

        # 构造单日大跌数据（跌幅 >= 9%）
        import pandas as pd
        from datetime import datetime

        dates = pd.date_range(end=datetime.now(), periods=5, freq="D")
        data = {
            "日期": dates,
            "开盘": [10.0] * 5,
            "收盘": [10.0, 9.0, 8.0, 7.0, 6.3],  # 最后一天跌幅 10%
            "涨跌幅": [0, -10.0, -11.11, -12.5, -10.0],  # 多个单日大跌
        }
        df = pd.DataFrame(data)

        with patch("akshare.stock_zh_a_hist") as mock_api:
            mock_api.return_value = df

            risk = await processor._check_price_risk()

            assert risk is not None
            assert risk["type"] == "价格风险"
            assert risk["level"] == "高"
            assert "单日大跌" in risk["detail"]

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_check_price_risk_medium(self):
        """测试价格风险检查 - 中风险"""
        processor = RiskProcessor("000001", days=3)

        # 构造连续下跌数据（单日跌幅 < 9%）
        import pandas as pd
        from datetime import datetime, timedelta

        dates = pd.date_range(end=datetime.now(), periods=5, freq="D")
        data = {
            "日期": dates,
            "开盘": [10.0] * 5,
            "收盘": [10.0, 9.6, 9.2, 8.8, 8.5],
            "涨跌幅": [0, -4.0, -4.17, -4.35, -3.41],  # 累计 > 10%，单日 < 9%
        }
        df = pd.DataFrame(data)

        with patch("akshare.stock_zh_a_hist") as mock_api:
            mock_api.return_value = df

            risk = await processor._check_price_risk()

            assert risk is not None
            assert risk["type"] == "价格风险"
            assert risk["level"] == "中"
            assert "连续下跌" in risk["detail"]

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_check_flow_risk_high(self):
        """测试资金风险检查 - 高风险"""
        processor = RiskProcessor("000001")

        # 构造单日大额流出数据（>= 5亿）
        import pandas as pd
        from datetime import datetime

        dates = pd.date_range(end=datetime.now(), periods=5, freq="D")
        data = {
            "日期": dates,
            "收盘价": [10.0] * 5,
            "涨跌幅": [0] * 5,
            "主力净流入-净额": [0, 0, 0, 0, -6e8],  # 最后一天流出 6 亿
            "主力净流入-净占比": [-1.0] * 5,
            "超大单净流入-净额": [0] * 5,
            "超大单净流入-净占比": [0] * 5,
            "大单净流入-净额": [0] * 5,
            "大单净流入-净占比": [0] * 5,
            "中单净流入-净额": [0] * 5,
            "中单净流入-净占比": [0] * 5,
            "小单净流入-净额": [0] * 5,
            "小单净流入-净占比": [0] * 5,
        }
        df = pd.DataFrame(data)

        with patch("akshare.stock_individual_fund_flow") as mock_api:
            mock_api.return_value = df

            risk = await processor._check_flow_risk()

            # 单日流出 6 亿
            assert risk is not None
            assert risk["type"] == "资金风险"
            assert risk["level"] == "高"
            assert "单日" in risk["detail"]

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_check_flow_risk_medium(self):
        """测试资金风险检查 - 中风险"""
        processor = RiskProcessor("000001", days=5)

        # 构造连续流出数据（单日 < 5 亿，累计 > 1 亿）
        import pandas as pd
        from datetime import datetime

        dates = pd.date_range(end=datetime.now(), periods=5, freq="D")
        data = {
            "日期": dates,
            "收盘价": [10.0] * 5,
            "涨跌幅": [0] * 5,
            "主力净流入-净额": [-2e8, -1.5e8, -1e8, 0.5e8, -0.5e8],
            "主力净流入-净占比": [-1.0] * 5,
            "超大单净流入-净额": [0] * 5,
            "超大单净流入-净占比": [0] * 5,
            "大单净流入-净额": [0] * 5,
            "大单净流入-净占比": [0] * 5,
            "中单净流入-净额": [0] * 5,
            "中单净流入-净占比": [0] * 5,
            "小单净流入-净额": [0] * 5,
            "小单净流入-净占比": [0] * 5,
        }
        df = pd.DataFrame(data)

        with patch("akshare.stock_individual_fund_flow") as mock_api:
            mock_api.return_value = df

            risk = await processor._check_flow_risk()

            assert risk is not None
            assert risk["type"] == "资金风险"
            assert risk["level"] == "中"
            assert "连续" in risk["detail"]
