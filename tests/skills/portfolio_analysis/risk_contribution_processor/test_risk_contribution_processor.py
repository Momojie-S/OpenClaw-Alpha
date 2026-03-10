# -*- coding: utf-8 -*-
"""风险贡献 Processor 测试"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import AsyncMock, patch

from openclaw_alpha.core.registry import DataSourceRegistry
from openclaw_alpha.data_sources import AkshareDataSource
from openclaw_alpha.skills.portfolio_analysis.risk_contribution_processor.risk_contribution_processor import (
    RiskContributionProcessor,
    RiskContributionResult,
    process,
)


@pytest.fixture(autouse=True)
def reset_registry():
    """每个测试前重置注册表"""
    registry = DataSourceRegistry.get_instance()
    registry.reset()
    registry.register(AkshareDataSource)
    yield
    registry.reset()


@pytest.fixture
def mock_price_data():
    """模拟价格数据"""
    dates = pd.date_range("2024-01-01", periods=30, freq="D")

    # 创建不同波动率的股票数据
    np.random.seed(42)
    data = {
        "000001": pd.DataFrame(
            {
                "date": dates,
                "close": 100 + np.random.randn(30).cumsum() * 0.5,
            }
        ),
        "600000": pd.DataFrame(
            {
                "date": dates,
                "close": 50 + np.random.randn(30).cumsum() * 1.0,
            }
        ),
        "002475": pd.DataFrame(
            {
                "date": dates,
                "close": 30 + np.random.randn(30).cumsum() * 1.5,
            }
        ),
    }

    return data


class TestRiskContributionProcessor:
    """测试 RiskContributionProcessor"""

    def test_init(self):
        """测试初始化"""
        processor = RiskContributionProcessor()
        assert processor is not None

    def test_validate_weights(self):
        """测试权重验证"""
        processor = RiskContributionProcessor()

        # 正常权重
        weights = processor._validate_weights({"A": 0.5, "B": 0.3, "C": 0.2})
        assert abs(weights.sum() - 1.0) < 0.01

        # 权重之和不为 1（会自动归一化）
        weights2 = processor._validate_weights({"A": 50, "B": 30, "C": 20})
        assert abs(weights2.sum() - 1.0) < 0.01

        # 负权重
        with pytest.raises(ValueError, match="权重不能为负数"):
            processor._validate_weights({"A": -0.5, "B": 1.0})

        # 权重之和为 0
        with pytest.raises(ValueError, match="权重之和不能为 0"):
            processor._validate_weights({"A": 0, "B": 0})

    def test_calculate_returns(self):
        """测试收益率计算"""
        processor = RiskContributionProcessor()

        price_data = {
            "000001": pd.DataFrame(
                {
                    "date": pd.date_range("2024-01-01", periods=10, freq="D"),
                    "close": [100, 101, 102, 101, 103, 104, 103, 105, 106, 107],
                }
            )
        }

        returns = processor._calculate_returns(price_data)

        assert "000001" in returns.columns
        assert len(returns) == 9

    def test_calculate_risk_parity_weights(self):
        """测试风险平价权重计算"""
        processor = RiskContributionProcessor()

        # 创建协方差矩阵
        cov = np.array(
            [
                [0.01, 0.002, 0.001],
                [0.002, 0.02, 0.003],
                [0.001, 0.003, 0.03],
            ]
        )

        weights = processor._calculate_risk_parity_weights(cov)

        # 权重之和应该为 1
        assert abs(weights.sum() - 1.0) < 0.01

        # 波动率高的资产权重应该更低
        # 第一个资产波动率最低，权重应该最高
        assert weights[0] > weights[1]
        assert weights[1] > weights[2]

    def test_calculate_risk_concentration(self):
        """测试风险集中度计算"""
        processor = RiskContributionProcessor()

        # 高度集中
        risk_pct = np.array([0.5, 0.3, 0.15, 0.05])
        conc1, level1 = processor._calculate_risk_concentration(risk_pct)
        assert abs(conc1 - 0.95) < 0.01  # 0.5 + 0.3 + 0.15
        assert level1 == "风险集中"

        # 适度分散
        risk_pct2 = np.array([0.35, 0.25, 0.2, 0.2])
        conc2, level2 = processor._calculate_risk_concentration(risk_pct2)
        assert abs(conc2 - 0.8) < 0.01
        assert level2 == "风险集中"

        # 高度分散
        risk_pct3 = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        conc3, level3 = processor._calculate_risk_concentration(risk_pct3)
        assert abs(conc3 - 0.6) < 0.01
        assert level3 == "适度分散"

    def test_generate_suggestion(self):
        """测试投资建议生成"""
        processor = RiskContributionProcessor()

        from openclaw_alpha.skills.portfolio_analysis.risk_contribution_processor.risk_contribution_processor import (
            RiskContribution,
        )

        # 风险集中
        stocks = [
            RiskContribution("A", 0.5, 0.01, 0.6, 0.3, -0.2),
            RiskContribution("B", 0.3, 0.005, 0.3, 0.35, 0.05),
            RiskContribution("C", 0.2, 0.003, 0.1, 0.35, 0.15),
        ]

        suggestion = processor._generate_suggestion(stocks, "风险集中")
        assert "风险高度集中" in suggestion
        assert "A" in suggestion

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_analyze_with_mock(self, mock_price_data):
        """测试分析功能（使用 mock 数据）"""
        processor = RiskContributionProcessor()

        holdings = {"000001": 0.5, "600000": 0.3, "002475": 0.2}

        # Mock 获取价格数据
        with patch.object(
            processor,
            "_fetch_prices",
            new_callable=AsyncMock,
            return_value=mock_price_data,
        ):
            result = await processor.analyze(holdings)

        assert isinstance(result, RiskContributionResult)
        assert len(result.stocks) == 3
        assert result.portfolio_volatility > 0
        assert 0 <= result.risk_concentration <= 1


class TestProcess:
    """测试便捷函数"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_process_text_format(self, mock_price_data):
        """测试文本格式输出"""
        holdings = {"000001": 0.5, "600000": 0.3, "002475": 0.2}

        with patch(
            "openclaw_alpha.skills.portfolio_analysis.risk_contribution_processor.risk_contribution_processor.fetch_prices",
            new_callable=AsyncMock,
            return_value=mock_price_data,
        ):
            result = await process(holdings, days=30, output_format="text")

        assert isinstance(result, str)
        assert "风险贡献分析报告" in result
        assert "风险集中度" in result

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_process_json_format(self, mock_price_data):
        """测试 JSON 格式输出"""
        holdings = {"000001": 0.5, "600000": 0.3, "002475": 0.2}

        with patch(
            "openclaw_alpha.skills.portfolio_analysis.risk_contribution_processor.risk_contribution_processor.fetch_prices",
            new_callable=AsyncMock,
            return_value=mock_price_data,
        ):
            result = await process(holdings, days=30, output_format="json")

        assert isinstance(result, dict)
        assert "stocks" in result
        assert "portfolio_volatility" in result
        assert "risk_concentration" in result
