# -*- coding: utf-8 -*-
"""IndexProcessor 测试"""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

# 添加路径
import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "skills"))
sys.path.insert(0, str(project_root / "src"))


class TestIndexProcessor:
    """IndexProcessor 测试类"""

    @pytest.fixture
    def sample_indices_data(self):
        """模拟指数数据"""
        return {
            "sh000001": [
                {"date": f"2026-03-0{i}", "open": 3300 + i*10, "high": 3310 + i*10, "low": 3295 + i*10, "close": 3305 + i*10, "volume": 300000000, "amount": 35000000000}
                for i in range(1, 7)
            ] + [
                {"date": "2026-03-06", "open": 3480, "high": 3495, "low": 3475, "close": 3490.55, "volume": 405000000, "amount": 48000000000}
            ]
        }

    @pytest.fixture
    def processor(self):
        """创建处理器实例"""
        from skills.index_analysis.scripts.index_processor.index_processor import IndexProcessor
        return IndexProcessor(date="2026-03-06", top_n=6)

    def test_calc_ma_basic(self, processor):
        """测试均线计算 - 基本场景"""
        data = [
            {"close": 100},
            {"close": 101},
            {"close": 102},
            {"close": 103},
            {"close": 104},
        ]
        ma5 = processor._calc_ma(data, 5)
        assert ma5 == 102.0  # (100+101+102+103+104)/5

    def test_calc_ma_insufficient_data(self, processor):
        """测试均线计算 - 数据不足"""
        data = [
            {"close": 100},
            {"close": 101},
        ]
        ma5 = processor._calc_ma(data, 5)
        assert ma5 is None

    def test_calc_ma_empty_data(self, processor):
        """测试均线计算 - 空数据"""
        ma5 = processor._calc_ma([], 5)
        assert ma5 is None

    def test_judge_trend_strong_up(self, processor):
        """测试趋势判断 - 强势上涨"""
        trend = processor._judge_trend(
            close=3500, ma5=3480, ma20=3400, change_pct=1.5
        )
        assert trend == "强势上涨"

    def test_judge_trend_oscillating_up(self, processor):
        """测试趋势判断 - 震荡上涨"""
        trend = processor._judge_trend(
            close=3450, ma5=3440, ma20=3400, change_pct=0.5
        )
        assert trend == "震荡上涨"

    def test_judge_trend_oscillating(self, processor):
        """测试趋势判断 - 震荡"""
        # 震荡条件：MA5 和 MA20 接近（差距 < 1%），涨跌幅 < 1%
        trend = processor._judge_trend(
            close=3400, ma5=3398, ma20=3397, change_pct=0.3
        )
        assert trend == "震荡"

    def test_judge_trend_oscillating_down(self, processor):
        """测试趋势判断 - 震荡下跌"""
        trend = processor._judge_trend(
            close=3350, ma5=3380, ma20=3420, change_pct=-0.5
        )
        assert trend == "震荡下跌"

    def test_judge_trend_weak_down(self, processor):
        """测试趋势判断 - 弱势下跌"""
        trend = processor._judge_trend(
            close=3300, ma5=3350, ma20=3400, change_pct=-2.0
        )
        assert trend == "弱势下跌"

    def test_judge_trend_insufficient_data(self, processor):
        """测试趋势判断 - 数据不足"""
        trend = processor._judge_trend(
            close=3500, ma5=None, ma20=3400, change_pct=1.5
        )
        assert trend == "数据不足"

    def test_calc_market_temperature_overheated(self, processor):
        """测试市场温度 - 过热"""
        indices = [
            {"change_pct": 2.5},
            {"change_pct": 3.0},
            {"change_pct": 2.2},
        ]
        temperature = processor._calc_market_temperature(indices)
        assert temperature == "过热"

    def test_calc_market_temperature_warm(self, processor):
        """测试市场温度 - 温热"""
        indices = [
            {"change_pct": 1.5},
            {"change_pct": 1.2},
            {"change_pct": 0.5},
        ]
        temperature = processor._calc_market_temperature(indices)
        assert temperature == "温热"

    def test_calc_market_temperature_normal(self, processor):
        """测试市场温度 - 正常"""
        indices = [
            {"change_pct": 0.5},
            {"change_pct": -0.3},
            {"change_pct": 0.8},
        ]
        temperature = processor._calc_market_temperature(indices)
        assert temperature == "正常"

    def test_calc_market_temperature_cold(self, processor):
        """测试市场温度 - 偏冷"""
        indices = [
            {"change_pct": -1.5},
            {"change_pct": -1.2},
            {"change_pct": 0.5},
        ]
        temperature = processor._calc_market_temperature(indices)
        assert temperature == "偏冷"

    def test_calc_market_temperature_freezing(self, processor):
        """测试市场温度 - 过冷"""
        indices = [
            {"change_pct": -2.5},
            {"change_pct": -3.0},
            {"change_pct": -2.2},
        ]
        temperature = processor._calc_market_temperature(indices)
        assert temperature == "过冷"

    def test_calc_overall_trend_strong(self, processor):
        """测试整体趋势 - 强势"""
        indices = [
            {"trend": "强势上涨"},
            {"trend": "震荡上涨"},
            {"trend": "强势上涨"},
            {"trend": "震荡上涨"},
            {"trend": "震荡"},
        ]
        trend = processor._calc_overall_trend(indices)
        assert trend == "强势"

    def test_calc_overall_trend_weak(self, processor):
        """测试整体趋势 - 弱势"""
        indices = [
            {"trend": "弱势下跌"},
            {"trend": "震荡下跌"},
            {"trend": "弱势下跌"},
            {"trend": "震荡下跌"},
            {"trend": "震荡"},
        ]
        trend = processor._calc_overall_trend(indices)
        assert trend == "弱势"

    def test_calc_overall_trend_oscillating(self, processor):
        """测试整体趋势 - 震荡"""
        indices = [
            {"trend": "震荡"},
            {"trend": "震荡"},
            {"trend": "震荡"},
        ]
        trend = processor._calc_overall_trend(indices)
        assert trend == "震荡"

    def test_format_number_large(self, processor):
        """测试数字格式化 - 大数"""
        result = processor._format_number(500000000, 100000000, "股")
        assert "5.0" in result

    def test_format_number_medium(self, processor):
        """测试数字格式化 - 中等数"""
        result = processor._format_number(5000, 1, "")
        assert "5000" in result

    def test_format_number_zero(self, processor):
        """测试数字格式化 - 零"""
        result = processor._format_number(0, 1, "")
        assert result == "0"


class TestIndexFetcher:
    """IndexFetcher 测试类"""

    @pytest.fixture
    def sample_raw_data(self):
        """模拟 AKShare 原始数据"""
        import pandas as pd
        return pd.DataFrame([
            {"date": "2026-03-04", "open": 3470.0, "high": 3485.0, "low": 3465.0, "close": 3480.30, "volume": 400000000, "amount": 47500000000},
            {"date": "2026-03-05", "open": 3480.0, "high": 3495.0, "low": 3475.0, "close": 3490.55, "volume": 405000000, "amount": 48000000000},
            {"date": "2026-03-06", "open": 3490.0, "high": 3505.0, "low": 3485.0, "close": 3500.80, "volume": 410000000, "amount": 48500000000},
        ])

    def test_transform_basic(self, sample_raw_data):
        """测试数据转换 - 基本场景"""
        from skills.index_analysis.scripts.index_fetcher.akshare import IndexFetcherAkshare

        fetcher = IndexFetcherAkshare()
        result = fetcher._transform(sample_raw_data)

        assert len(result) == 3
        assert result[0]["date"] == "2026-03-04"
        assert result[0]["open"] == 3470.0
        assert result[0]["close"] == 3480.30

    def test_transform_empty_data(self):
        """测试数据转换 - 空数据"""
        from skills.index_analysis.scripts.index_fetcher.akshare import IndexFetcherAkshare
        import pandas as pd

        fetcher = IndexFetcherAkshare()
        result = fetcher._transform(pd.DataFrame())

        assert result == []

    def test_transform_none_data(self):
        """测试数据转换 - None"""
        from skills.index_analysis.scripts.index_fetcher.akshare import IndexFetcherAkshare

        fetcher = IndexFetcherAkshare()
        result = fetcher._transform(None)

        assert result == []

    def test_transform_sorted_by_date(self, sample_raw_data):
        """测试数据转换 - 按日期排序"""
        from skills.index_analysis.scripts.index_fetcher.akshare import IndexFetcherAkshare

        fetcher = IndexFetcherAkshare()
        result = fetcher._transform(sample_raw_data)

        # 验证排序（旧到新）
        dates = [r["date"] for r in result]
        assert dates == sorted(dates)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
