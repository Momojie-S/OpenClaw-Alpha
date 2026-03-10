# -*- coding: utf-8 -*-
"""市场宽度分析测试"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from openclaw_alpha.skills.market_sentiment.breadth_fetcher import (
    BreadthData,
    BreadthFetcher,
    fetch,
)
from openclaw_alpha.skills.market_sentiment.breadth_processor import (
    process,
    _calc_health_level,
    _calc_trend,
    _detect_signals,
)


@pytest.fixture
def sample_breadth_data():
    """模拟市场宽度数据"""
    return [
        BreadthData(
            date="2026-03-05",
            close=4124.19,
            high20=541,
            low20=95,
            high60=383,
            low60=26,
            high120=277,
            low120=17,
        ),
        BreadthData(
            date="2026-03-04",
            close=4108.57,
            high20=339,
            low20=385,
            high60=245,
            low60=184,
            high120=188,
            low120=131,
        ),
        BreadthData(
            date="2026-03-03",
            close=4082.47,
            high20=223,
            low20=2193,
            high60=173,
            low60=1061,
            high120=140,
            low120=778,
        ),
        BreadthData(
            date="2026-03-02",
            close=4122.68,
            high20=272,
            low20=2350,
            high60=217,
            low60=941,
            high120=163,
            low120=649,
        ),
        BreadthData(
            date="2026-03-01",
            close=4182.59,
            high20=636,
            low20=1284,
            high60=469,
            low60=465,
            high120=361,
            low120=320,
        ),
        BreadthData(
            date="2026-02-26",
            close=4162.88,
            high20=914,
            low20=182,
            high60=686,
            low60=70,
            high120=440,
            low120=51,
        ),
        BreadthData(
            date="2026-02-25",
            close=4146.63,
            high20=874,
            low20=327,
            high60=688,
            low60=127,
            high120=445,
            low120=82,
        ),
        BreadthData(
            date="2026-02-24",
            close=4147.23,
            high20=709,
            low20=94,
            high60=550,
            low60=27,
            high120=344,
            low120=17,
        ),
        BreadthData(
            date="2026-02-23",
            close=4117.41,
            high20=610,
            low20=264,
            high60=459,
            low60=68,
            high120=301,
            low120=46,
        ),
        BreadthData(
            date="2026-02-12",
            close=4082.07,
            high20=232,
            low20=687,
            high60=177,
            low60=186,
            high120=130,
            low120=129,
        ),
    ]


class TestBreadthData:
    """BreadthData 数据类测试"""

    def test_breadth_ratio_20(self, sample_breadth_data):
        """测试20日宽度比率计算"""
        data = sample_breadth_data[0]
        # high20=541, low20=95, ratio = 541/(541+95) = 0.8507
        assert abs(data.breadth_ratio_20 - 0.8507) < 0.01

    def test_breadth_ratio_60(self, sample_breadth_data):
        """测试60日宽度比率计算"""
        data = sample_breadth_data[0]
        # high60=383, low60=26, ratio = 383/(383+26) = 0.9364
        assert abs(data.breadth_ratio_60 - 0.9364) < 0.01

    def test_breadth_ratio_120(self, sample_breadth_data):
        """测试120日宽度比率计算"""
        data = sample_breadth_data[0]
        # high120=277, low120=17, ratio = 277/(277+17) = 0.9422
        assert abs(data.breadth_ratio_120 - 0.9422) < 0.01

    def test_breadth_ratio_zero_division(self):
        """测试除零保护"""
        data = BreadthData(
            date="2026-03-05",
            close=4000.0,
            high20=0,
            low20=0,
            high60=0,
            low60=0,
            high120=0,
            low120=0,
        )
        assert data.breadth_ratio_20 == 0.5
        assert data.breadth_ratio_60 == 0.5
        assert data.breadth_ratio_120 == 0.5


class TestCalcHealthLevel:
    """健康度计算测试"""

    def test_healthy_level(self):
        """测试健康等级"""
        level, score = _calc_health_level(0.8)
        assert level == "健康"
        assert score == 80.0

    def test_normal_level(self):
        """测试正常等级"""
        level, score = _calc_health_level(0.6)
        assert level == "正常"
        assert score == 60.0

    def test_weak_level(self):
        """测试偏弱等级"""
        level, score = _calc_health_level(0.4)
        assert level == "偏弱"
        assert score == 40.0

    def test_danger_level(self):
        """测试危险等级"""
        level, score = _calc_health_level(0.2)
        assert level == "危险"
        assert score == 10.0


class TestCalcTrend:
    """趋势计算测试"""

    def test_rising_trend(self, sample_breadth_data):
        """测试上升趋势"""
        # 反转数据（需要按日期升序）
        data_list = list(reversed(sample_breadth_data))
        trend, change = _calc_trend(data_list)
        assert trend == "上升"  # 最近5日比前5日高
        assert change > 0.1

    def test_falling_trend(self, sample_breadth_data):
        """测试下降趋势"""
        # 直接使用原始数据（按日期降序）
        trend, change = _calc_trend(sample_breadth_data)
        assert trend == "下降"  # 最近5日比前5日低
        assert change < -0.1

    def test_stable_trend(self, sample_breadth_data):
        """测试平稳趋势"""
        # 修改数据使趋势平稳
        stable_data = []
        for i, d in enumerate(sample_breadth_data[:10]):
            stable_data.append(
                BreadthData(
                    date=d.date,
                    close=d.close,
                    high20=100,
                    low20=100,  # 比率都是 0.5
                    high60=100,
                    low60=100,
                    high120=100,
                    low120=100,
                )
            )
        trend, change = _calc_trend(stable_data)
        assert trend == "平稳"
        assert abs(change) <= 0.1

    def test_insufficient_data(self):
        """测试数据不足"""
        data = [
            BreadthData(
                date="2026-03-05",
                close=4100.0,
                high20=100,
                low20=100,
                high60=100,
                low60=100,
                high120=100,
                low120=100,
            )
        ]
        trend, change = _calc_trend(data)
        assert trend is None
        assert change is None


class TestDetectSignals:
    """信号检测测试"""

    def test_extremely_healthy_signal(self, sample_breadth_data):
        """测试极度健康信号"""
        # high20=541, low20=95, ratio=0.85
        signals = _detect_signals(sample_breadth_data[0], sample_breadth_data)
        assert any("极度健康" in s for s in signals)

    def test_extremely_danger_signal(self):
        """测试极度危险信号"""
        current = BreadthData(
            date="2026-03-05",
            close=4000.0,
            high20=50,
            low20=450,  # ratio = 0.1
            high60=30,
            low60=470,
            high120=20,
            low120=480,
        )
        signals = _detect_signals(current, [current])
        assert any("极度危险" in s for s in signals)

    def test_top_divergence_signal(self, sample_breadth_data):
        """测试顶背离信号"""
        # 创建顶背离场景：指数上涨但宽度下降
        # data_list = [current] + sample_breadth_data
        # 所以 data_list[4] = sample_breadth_data[3] (2026-03-02)
        prev = sample_breadth_data[3]  # 2026-03-02
        # prev.breadth_ratio_20 = 272/(272+2350) = 0.1037
        # 要触发顶背离，current.breadth_ratio < 0.1037 - 0.1 = 0.0037 (几乎不可能)
        # 所以需要修改 prev 数据使其 breadth_ratio 更高
        
        # 修改 prev 数据使其有更高的 breadth_ratio
        high_ratio_prev = BreadthData(
            date="2026-03-02",
            close=4000.0,
            high20=800,
            low20=200,  # breadth_ratio = 0.8
            high60=400,
            low60=100,
            high120=200,
            low120=50,
        )
        
        current = BreadthData(
            date="2026-03-06",
            close=4200.0,  # 比 prev.close 高
            high20=100,
            low20=400,  # 宽度比率 = 0.2，比 0.8 - 0.1 = 0.7 低
            high60=50,
            low60=200,
            high120=25,
            low120=100,
        )
        
        # 构建 data_list，使 data_list[4] = high_ratio_prev
        data_list = [
            current,
            sample_breadth_data[0],
            sample_breadth_data[1],
            sample_breadth_data[2],
            high_ratio_prev,  # data_list[4]
            sample_breadth_data[4],
        ]
        
        signals = _detect_signals(current, data_list)
        # current.close=4200 > prev.close=4000
        # current.breadth_ratio=0.2 < 0.8 - 0.1 = 0.7
        assert any("顶背离" in s for s in signals)

    def test_bottom_divergence_signal(self, sample_breadth_data):
        """测试底背离信号"""
        # 创建底背离场景：指数下跌但宽度上升
        current = BreadthData(
            date="2026-03-06",
            close=3900.0,  # 比之前低
            high20=400,
            low20=100,  # 宽度比率 0.8，比之前高
            high60=200,
            low60=50,
            high120=100,
            low120=25,
        )
        prev = sample_breadth_data[4]  # 5个交易日前
        data_list = [current] + sample_breadth_data[:4] + [prev]
        signals = _detect_signals(current, data_list)
        assert any("底背离" in s for s in signals)

    def test_high_exceeds_low_signal(self, sample_breadth_data):
        """测试新高远超新低信号"""
        signals = _detect_signals(sample_breadth_data[0], sample_breadth_data)
        # high20=541, low20=95, 541/95=5.69 > 3
        assert any("远超新低" in s for s in signals)


class TestProcess:
    """Processor 测试"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_process_with_mock(self, sample_breadth_data):
        """测试处理流程（mock 数据）"""
        with patch(
            "skills.market_sentiment.scripts.breadth_processor.breadth_processor.fetch_breadth"
        ) as mock_fetch:
            mock_fetch.return_value = sample_breadth_data

            result = await process(symbol="all", days=10, output_json=False)

            assert result["date"] == "2026-03-05"
            assert result["close"] == 4124.19
            assert "breadth" in result
            assert "health" in result
            assert "signals" in result

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_process_empty_data(self):
        """测试空数据处理"""
        with patch(
            "skills.market_sentiment.scripts.breadth_processor.breadth_processor.fetch_breadth"
        ) as mock_fetch:
            mock_fetch.return_value = []

            result = await process(symbol="all", days=10, output_json=False)

            assert "error" in result
