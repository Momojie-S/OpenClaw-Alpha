# -*- coding: utf-8 -*-
"""定投建议 Processor 单元测试"""

import pytest
from unittest.mock import AsyncMock, patch

from openclaw_alpha.skills.smart_dip.dip_advice_processor.dip_advice_processor import (
    get_multiplier,
    get_dip_advice,
    format_text,
)


class TestGetMultiplier:
    """测试定投倍数计算"""

    def test_extreme_undervaluation(self):
        """极度低估"""
        multiplier, status, action = get_multiplier(3.5)
        assert multiplier == 2.0
        assert status == "极度低估"
        assert action == "大幅加仓"

    def test_undervaluation(self):
        """低估"""
        multiplier, status, action = get_multiplier(2.5)
        assert multiplier == 1.5
        assert status == "低估"
        assert action == "增加定投"

    def test_reasonable_low(self):
        """合理（接近低估边界）"""
        multiplier, status, action = get_multiplier(1.5)
        assert multiplier == 1.0
        assert status == "合理"
        assert action == "正常定投"

    def test_reasonable_high(self):
        """合理（接近高估边界）"""
        multiplier, status, action = get_multiplier(0.5)
        assert multiplier == 1.0
        assert status == "合理"
        assert action == "正常定投"

    def test_overvaluation(self):
        """高估"""
        multiplier, status, action = get_multiplier(-0.5)
        assert multiplier == 0.5
        assert status == "高估"
        assert action == "减半定投"

    def test_extreme_overvaluation(self):
        """极度高估"""
        multiplier, status, action = get_multiplier(-1.5)
        assert multiplier == 0.0
        assert status == "极度高估"
        assert action == "暂停定投"

    def test_boundary_values(self):
        """边界值测试"""
        # 边界：3%
        # > 3.0 → 2.0
        assert get_multiplier(3.0)[0] == 1.5  # 等于 3% 是低估（3.0 > 2.0）
        assert get_multiplier(3.01)[0] == 2.0

        # 边界：2%
        # > 2.0 → 1.5
        assert get_multiplier(2.0)[0] == 1.0  # 等于 2% 是合理（2.0 不 > 2.0，但 > 0.0）
        assert get_multiplier(2.01)[0] == 1.5

        # 边界：0%
        # > 0.0 → 1.0
        assert get_multiplier(0.0)[0] == 0.5  # 等于 0% 是高估（0.0 不 > 0.0，但 > -1.0）
        assert get_multiplier(0.01)[0] == 1.0  # 大于 0% 才是合理

        # 边界：-1%
        # > -1.0 → 0.5
        assert get_multiplier(-1.0)[0] == 0.0  # 等于 -1% 是极度高估
        assert get_multiplier(-0.99)[0] == 0.5  # 大于 -1% 是高估


class TestGetDipAdvice:
    """测试定投建议获取"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_success(self):
        """成功获取定投建议"""
        mock_ebr_data = {
            "date": "2026-03-06",
            "risk_premium": 2.5,
            "percentile": 25,
        }

        with patch(
            "openclaw_alpha.skills.smart_dip.dip_advice_processor.dip_advice_processor.EquityBondRatioProcessor"
        ) as mock_processor_class:
            mock_processor = AsyncMock()
            mock_processor.process.return_value = mock_ebr_data
            mock_processor_class.return_value = mock_processor

            result = await get_dip_advice("2026-03-06", 1000, "fed_model")

            assert result["date"] == "2026-03-06"
            assert result["base_amount"] == 1000
            assert result["valuation"]["equity_bond_ratio"] == 2.5
            assert result["valuation"]["status"] == "低估"
            assert result["recommendation"]["multiplier"] == 1.5
            assert result["recommendation"]["amount"] == 1500

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_error_handling(self):
        """错误处理"""
        mock_ebr_data = {
            "date": "2026-03-06",
            "error": "获取沪深300 PE失败",
        }

        with patch(
            "openclaw_alpha.skills.smart_dip.dip_advice_processor.dip_advice_processor.EquityBondRatioProcessor"
        ) as mock_processor_class:
            mock_processor = AsyncMock()
            mock_processor.process.return_value = mock_ebr_data
            mock_processor_class.return_value = mock_processor

            with pytest.raises(ValueError, match="获取股债性价比数据失败"):
                await get_dip_advice("2026-03-06", 1000, "fed_model")

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_missing_risk_premium(self):
        """缺少风险溢价数据"""
        mock_ebr_data = {
            "date": "2026-03-06",
        }

        with patch(
            "openclaw_alpha.skills.smart_dip.dip_advice_processor.dip_advice_processor.EquityBondRatioProcessor"
        ) as mock_processor_class:
            mock_processor = AsyncMock()
            mock_processor.process.return_value = mock_ebr_data
            mock_processor_class.return_value = mock_processor

            with pytest.raises(ValueError, match="无法获取股债性价比数据"):
                await get_dip_advice("2026-03-06", 1000, "fed_model")

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_percentile_based_multiplier(self):
        """基于分位数的倍数推断"""
        # 低分位 → 高倍数
        mock_ebr_data = {
            "date": "2026-03-06",
            "risk_premium": 4.0,
            "percentile": 20,
        }

        with patch(
            "openclaw_alpha.skills.smart_dip.dip_advice_processor.dip_advice_processor.EquityBondRatioProcessor"
        ) as mock_processor_class:
            mock_processor = AsyncMock()
            mock_processor.process.return_value = mock_ebr_data
            mock_processor_class.return_value = mock_processor

            result = await get_dip_advice("2026-03-06", 1000, "fed_model")

            assert result["history"]["avg_multiplier_3m"] == 1.5
            assert result["history"]["avg_multiplier_6m"] == 1.3


class TestFormatText:
    """测试文本格式化"""

    def test_format_complete_data(self):
        """格式化完整数据"""
        result = {
            "date": "2026-03-06",
            "base_amount": 2000,
            "valuation": {
                "equity_bond_ratio": 2.5,
                "status": "低估",
            },
            "recommendation": {
                "multiplier": 1.5,
                "amount": 3000,
                "action": "增加定投",
            },
            "history": {
                "avg_multiplier_3m": 1.2,
                "avg_multiplier_6m": 1.3,
            },
        }

        text = format_text(result)

        assert "智能定投建议" in text
        assert "2026-03-06" in text
        assert "2000 元" in text
        assert "2.50%" in text
        assert "低估" in text
        assert "1.5x" in text
        assert "3000 元" in text
        assert "增加定投" in text
        assert "1.2x" in text

    def test_format_missing_history(self):
        """格式化缺少历史数据的情况"""
        result = {
            "date": "2026-03-06",
            "base_amount": 1000,
            "valuation": {
                "equity_bond_ratio": 2.5,
                "status": "低估",
            },
            "recommendation": {
                "multiplier": 1.5,
                "amount": 1500,
                "action": "增加定投",
            },
            "history": {
                "avg_multiplier_3m": None,
                "avg_multiplier_6m": None,
            },
        }

        text = format_text(result)

        assert "暂无数据" in text
