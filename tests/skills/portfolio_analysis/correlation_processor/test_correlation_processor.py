# -*- coding: utf-8 -*-
"""持仓相关性 Processor 测试"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import AsyncMock, patch

from openclaw_alpha.core.registry import DataSourceRegistry
from openclaw_alpha.data_sources import AkshareDataSource
from openclaw_alpha.skills.portfolio_analysis.correlation_processor.correlation_processor import (
    CorrelationProcessor,
    CorrelationResult,
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

    # 创建相关性不同的股票数据
    data = {
        "000001": pd.DataFrame(
            {
                "date": dates,
                "close": np.random.randn(30).cumsum() + 100,
            }
        ),
        "600000": pd.DataFrame(
            {
                "date": dates,
                "close": np.random.randn(30).cumsum() + 50,
            }
        ),
        "002475": pd.DataFrame(
            {
                "date": dates,
                "close": np.random.randn(30).cumsum() + 30,
            }
        ),
    }

    return data


class TestCorrelationProcessor:
    """测试 CorrelationProcessor"""

    def test_init(self):
        """测试初始化"""
        processor = CorrelationProcessor()
        assert processor is not None

    def test_calculate_returns(self):
        """测试收益率计算"""
        processor = CorrelationProcessor()

        # 模拟价格数据
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
        assert len(returns) == 9  # 10 天数据会产生 9 个收益率

    def test_calculate_returns_insufficient_data(self):
        """测试数据不足时的收益率计算"""
        processor = CorrelationProcessor()

        # 只有 1 天数据
        price_data = {
            "000001": pd.DataFrame(
                {
                    "date": pd.date_range("2024-01-01", periods=1, freq="D"),
                    "close": [100],
                }
            )
        }

        with pytest.raises(ValueError, match="无法计算任何股票的收益率"):
            processor._calculate_returns(price_data)

    def test_find_high_correlation_pairs(self):
        """测试高相关股票对查找"""
        processor = CorrelationProcessor()

        # 创建相关系数矩阵
        corr_matrix = pd.DataFrame(
            {
                "A": [1.0, 0.8, 0.3],
                "B": [0.8, 1.0, 0.5],
                "C": [0.3, 0.5, 1.0],
            },
            index=["A", "B", "C"],
        )

        pairs = processor._find_high_correlation_pairs(corr_matrix)

        # 应该找到 A-B（0.8）和 B-C（0.5）
        assert len(pairs) >= 1
        assert any(p.stock1 == "A" and p.stock2 == "B" for p in pairs)

    def test_calculate_avg_correlation(self):
        """测试平均相关性计算"""
        processor = CorrelationProcessor()

        # 创建相关系数矩阵
        corr_matrix = pd.DataFrame(
            {
                "A": [1.0, 0.6, 0.4],
                "B": [0.6, 1.0, 0.5],
                "C": [0.4, 0.5, 1.0],
            },
            index=["A", "B", "C"],
        )

        avg_corr = processor._calculate_avg_correlation(corr_matrix)

        # 平均值应该是 (0.6 + 0.4 + 0.5) / 3
        expected = (0.6 + 0.4 + 0.5) / 3
        assert abs(avg_corr - expected) < 0.01

    def test_calculate_diversification_score(self):
        """测试分散化评分计算"""
        processor = CorrelationProcessor()

        # 低相关性 → 高分散化
        score1, level1 = processor._calculate_diversification_score(0.2)
        assert score1 > 0.6
        assert level1 == "高度分散"

        # 中等相关性 → 适度分散
        score2, level2 = processor._calculate_diversification_score(0.4)
        assert 0.4 < score2 < 0.7
        assert level2 == "适度分散"

        # 高相关性 → 集中
        score3, level3 = processor._calculate_diversification_score(0.6)
        assert score3 < 0.5
        assert level3 == "集中度偏高"

    def test_generate_suggestion(self):
        """测试投资建议生成"""
        processor = CorrelationProcessor()

        from openclaw_alpha.skills.portfolio_analysis.correlation_processor.correlation_processor import (
            CorrelationPair,
        )

        # 高相关对
        high_pairs = [
            CorrelationPair("A", "B", 0.8, "高相关"),
        ]

        # 集中度偏高
        suggestion1 = processor._generate_suggestion(high_pairs, "集中度偏高", 5)
        assert "高相关股票" in suggestion1
        assert "集中度较高" in suggestion1

        # 高度分散
        suggestion2 = processor._generate_suggestion([], "高度分散", 10)
        assert "高度分散" in suggestion2

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_analyze_with_mock(self, mock_price_data):
        """测试分析功能（使用 mock 数据）"""
        processor = CorrelationProcessor()

        # Mock 获取价格数据
        with patch.object(
            processor,
            "_fetch_prices",
            new_callable=AsyncMock,
            return_value=mock_price_data,
        ):
            result = await processor.analyze(["000001", "600000", "002475"])

        assert isinstance(result, CorrelationResult)
        assert len(result.stocks) == 3
        assert 0 <= result.avg_correlation <= 1
        assert 0 <= result.diversification_score <= 1


class TestProcess:
    """测试便捷函数"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_process_text_format(self, mock_price_data):
        """测试文本格式输出"""
        with patch(
            "skills.portfolio_analysis.scripts.correlation_processor.correlation_processor.fetch_prices",
            new_callable=AsyncMock,
            return_value=mock_price_data,
        ):
            result = await process(
                ["000001", "600000", "002475"],
                days=30,
                output_format="text",
            )

        assert isinstance(result, str)
        assert "持仓相关性分析报告" in result
        assert "分散化评估" in result

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_process_json_format(self, mock_price_data):
        """测试 JSON 格式输出"""
        with patch(
            "skills.portfolio_analysis.scripts.correlation_processor.correlation_processor.fetch_prices",
            new_callable=AsyncMock,
            return_value=mock_price_data,
        ):
            result = await process(
                ["000001", "600000", "002475"],
                days=30,
                output_format="json",
            )

        assert isinstance(result, dict)
        assert "stocks" in result
        assert "avg_correlation" in result
        assert "diversification_score" in result
