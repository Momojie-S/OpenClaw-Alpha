# -*- coding: utf-8 -*-
"""市场综合分析 Processor 测试"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, AsyncMock

from openclaw_alpha.skills.market_overview.overview_processor.overview_processor import (
    MarketOverviewProcessor,
    OverviewReport,
    MacroData,
    SentimentData,
    SectorData,
    NorthboundData,
    Conclusion,
    IndexData,
    process
)


class TestMarketOverviewProcessor:
    """Processor 基础测试"""

    def test_init_default(self):
        """测试默认初始化"""
        processor = MarketOverviewProcessor()
        assert processor.date == datetime.now().strftime("%Y-%m-%d")
        assert processor.mode == "full"
        assert processor.errors == []

    def test_init_custom(self):
        """测试自定义初始化"""
        processor = MarketOverviewProcessor(date="2026-03-07", mode="quick")
        assert processor.date == "2026-03-07"
        assert processor.mode == "quick"


class TestDataLoading:
    """数据加载测试"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_load_macro_data_not_exist(self, tmp_path):
        """测试宏观数据不存在"""
        processor = MarketOverviewProcessor(date="2026-03-07", mode="quick")

        with patch("skills.market_overview.scripts.overview_processor.overview_processor.load_output", return_value=None):
            result = await processor._load_macro_data()
            assert result is None
            assert "index_analysis: 数据不存在" in processor.errors

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_load_macro_data_success(self):
        """测试宏观数据加载成功"""
        mock_data = {
            "date": "2026-03-07",
            "market_temperature": "正常",
            "overall_trend": "震荡",
            "indices": [
                {
                    "name": "上证指数",
                    "code": "sh000001",
                    "close": 3345.67,
                    "change_pct": 0.5,
                    "trend": "震荡"
                }
            ],
            "strongest": {"name": "创业板指", "change_pct": 1.2},
            "weakest": {"name": "上证指数", "change_pct": -0.3}
        }

        processor = MarketOverviewProcessor(date="2026-03-07")

        with patch("skills.market_overview.scripts.overview_processor.overview_processor.load_output", return_value=mock_data):
            result = await processor._load_macro_data()

            assert result is not None
            assert result.date == "2026-03-07"
            assert result.temperature == "正常"
            assert result.overall_trend == "震荡"
            assert len(result.indices) == 1
            assert result.indices[0].name == "上证指数"

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_load_sentiment_data_success(self):
        """测试情绪数据加载成功"""
        mock_data = {
            "status": "偏热",
            "temperature": 65,
            "limit": {"up": 85, "down": 12, "break_board": 5},
            "trend": {"up": 2500, "down": 1800},
            "flow": {"main_net_inflow": 25.3},
            "signals": ["过热预警"]
        }

        processor = MarketOverviewProcessor(date="2026-03-07")

        with patch("skills.market_overview.scripts.overview_processor.overview_processor.load_output", return_value=mock_data):
            result = await processor._load_sentiment_data()

            assert result is not None
            assert result.status == "偏热"
            assert result.temperature == 65
            assert result.limit_up == 85
            assert result.limit_down == 12
            assert result.main_net_inflow == 25.3
            assert "过热预警" in result.signals

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_load_northbound_data_success(self):
        """测试外资数据加载成功"""
        mock_data = {
            "total_flow": 44.0,
            "status": "流入",
            "sh_flow": 25.3,
            "sz_flow": 18.7,
            "top_inflow": [{"name": "贵州茅台", "hold_change": 85000}],
            "top_outflow": [{"name": "中国平安", "hold_change": -32000}]
        }

        processor = MarketOverviewProcessor(date="2026-03-07")

        with patch("skills.market_overview.scripts.overview_processor.overview_processor.load_output", return_value=mock_data):
            result = await processor._load_northbound_data()

            assert result is not None
            assert result.total_flow == 44.0
            assert result.status == "流入"
            assert len(result.top_inflow) == 1


class TestJudgment:
    """综合判断测试"""

    def test_generate_judgment_strong_up(self):
        """测试强势上涨判断"""
        processor = MarketOverviewProcessor(date="2026-03-07", mode="full")

        report = OverviewReport(
            date="2026-03-07",
            mode="full",
            generated_at="2026-03-08T00:00:00",
            overall={},
            macro=MacroData(
                date="2026-03-07",
                indices=[
                    IndexData(name="上证指数", code="sh000001", close=3345.67, change_pct=1.5, trend="强势上涨")
                ],
                temperature="温热",
                overall_trend="强势上涨"
            ),
            sentiment=SentimentData(
                status="偏热",
                temperature=70,
                limit_up=100,
                limit_down=10
            ),
            northbound=NorthboundData(
                total_flow=50.0,
                status="大幅流入"
            )
        )

        result = processor._generate_judgment(report)
        assert result["judgment"] == "强势上涨"
        assert result["confidence"] == 0.85

    def test_generate_judgment_weak_down(self):
        """测试弱势下跌判断"""
        processor = MarketOverviewProcessor(date="2026-03-07", mode="full")

        report = OverviewReport(
            date="2026-03-07",
            mode="full",
            generated_at="2026-03-08T00:00:00",
            overall={},
            macro=MacroData(
                date="2026-03-07",
                indices=[
                    IndexData(name="上证指数", code="sh000001", close=3345.67, change_pct=-1.5, trend="弱势下跌")
                ],
                temperature="过冷",
                overall_trend="弱势下跌"
            ),
            sentiment=SentimentData(
                status="偏冷",
                temperature=30,
                limit_up=10,
                limit_down=100
            ),
            northbound=NorthboundData(
                total_flow=-50.0,
                status="大幅流出"
            )
        )

        result = processor._generate_judgment(report)
        assert result["judgment"] == "弱势下跌"
        assert result["confidence"] == 0.85

    def test_generate_judgment_oscillation(self):
        """测试震荡判断"""
        processor = MarketOverviewProcessor(date="2026-03-07", mode="full")

        report = OverviewReport(
            date="2026-03-07",
            mode="full",
            generated_at="2026-03-08T00:00:00",
            overall={},
            macro=MacroData(
                date="2026-03-07",
                indices=[
                    IndexData(name="上证指数", code="sh000001", close=3345.67, change_pct=0.3, trend="震荡")
                ],
                temperature="正常",
                overall_trend="震荡"
            ),
            sentiment=SentimentData(
                status="正常",
                temperature=50,
                limit_up=50,
                limit_down=50
            ),
            northbound=NorthboundData(
                total_flow=5.0,
                status="平衡"
            )
        )

        result = processor._generate_judgment(report)
        assert result["judgment"] == "震荡上涨"


class TestConclusion:
    """综合结论测试"""

    def test_generate_conclusion_with_data(self):
        """测试有数据时的结论生成"""
        processor = MarketOverviewProcessor(date="2026-03-07", mode="full")

        report = OverviewReport(
            date="2026-03-07",
            mode="full",
            generated_at="2026-03-08T00:00:00",
            overall={},
            macro=MacroData(
                date="2026-03-07",
                indices=[],
                temperature="正常",
                overall_trend="震荡上涨",
                strongest={"name": "创业板指", "change_pct": 1.2}
            ),
            sentiment=SentimentData(
                status="偏热",
                temperature=65,
                limit_up=85,
                limit_down=12,
                signals=["过热预警"]
            ),
            northbound=NorthboundData(
                total_flow=44.0,
                status="流入"
            ),
            sectors=SectorData(
                industry_top=[{"name": "电子", "change_pct": 3.5, "trend": "加热中"}],
                concept_top=[{"name": "人工智能", "change_pct": 4.2, "up_ratio": 0.8}]
            )
        )

        result = processor._generate_conclusion(report)

        assert "震荡上涨" in result.summary
        assert "偏热" in result.summary
        assert "流入" in result.summary
        assert len(result.highlights) > 0
        assert "过热预警" in result.risks

    def test_generate_conclusion_no_data(self):
        """测试无数据时的结论生成"""
        processor = MarketOverviewProcessor(date="2026-03-07", mode="quick")

        report = OverviewReport(
            date="2026-03-07",
            mode="quick",
            generated_at="2026-03-08T00:00:00",
            overall={}
        )

        result = processor._generate_conclusion(report)
        assert result.summary == "数据不足，无法生成结论"
        assert len(result.highlights) == 0


class TestFormatReport:
    """报告格式化测试"""

    def test_format_report_basic(self):
        """测试基本报告格式化"""
        processor = MarketOverviewProcessor(date="2026-03-07", mode="quick")

        report = OverviewReport(
            date="2026-03-07",
            mode="quick",
            generated_at="2026-03-08T00:00:00",
            overall={"judgment": "震荡上涨", "confidence": 0.7},
            conclusion=Conclusion(
                summary="指数震荡，情绪偏热",
                highlights=["最强指数：创业板指"],
                risks=[]
            )
        )

        result = processor.format_report(report)

        assert "# 市场分析报告 - 2026-03-07" in result
        assert "震荡上涨" in result
        assert "指数震荡，情绪偏热" in result

    def test_format_report_with_errors(self):
        """测试包含错误的报告格式化"""
        processor = MarketOverviewProcessor(date="2026-03-07", mode="quick")

        report = OverviewReport(
            date="2026-03-07",
            mode="quick",
            generated_at="2026-03-08T00:00:00",
            overall={"judgment": "震荡", "confidence": 0.5},
            errors=["index_analysis: 数据不存在", "market_sentiment: 数据不存在"]
        )

        result = processor.format_report(report)

        assert "数据获取问题" in result
        assert "index_analysis: 数据不存在" in result


class TestProcess:
    """主入口测试"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_process_quick_mode(self):
        """测试快速模式"""
        with patch("skills.market_overview.scripts.overview_processor.overview_processor.load_output", return_value=None):
            result = await process(date="2026-03-07", mode="quick")

            assert result.date == "2026-03-07"
            assert result.mode == "quick"
            assert result.macro is None
            assert result.sentiment is None
            assert result.sectors is None
            assert result.northbound is None

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_process_full_mode(self):
        """测试完整模式"""
        with patch("skills.market_overview.scripts.overview_processor.overview_processor.load_output", return_value=None):
            result = await process(date="2026-03-07", mode="full")

            assert result.date == "2026-03-07"
            assert result.mode == "full"
            # full 模式也会尝试加载数据，但因为是 None 所以都是 None
            assert result.sectors is not None  # SectorData 会被创建，但内容为空
            assert result.northbound is None


class TestEdgeCases:
    """边界情况测试"""

    def test_parse_temperature(self):
        """测试温度解析"""
        processor = MarketOverviewProcessor()

        assert processor._parse_temperature("过热") == 90
        assert processor._parse_temperature("温热") == 70
        assert processor._parse_temperature("正常") == 50
        assert processor._parse_temperature("偏冷") == 30
        assert processor._parse_temperature("过冷") == 10
        assert processor._parse_temperature("未知") == 50

    def test_format_report_with_full_data(self):
        """测试完整数据的报告格式化"""
        processor = MarketOverviewProcessor(date="2026-03-07", mode="full")

        report = OverviewReport(
            date="2026-03-07",
            mode="full",
            generated_at="2026-03-08T00:00:00",
            overall={"judgment": "震荡上涨", "confidence": 0.7},
            macro=MacroData(
                date="2026-03-07",
                indices=[
                    IndexData(name="上证指数", code="sh000001", close=3345.67, change_pct=0.5, trend="震荡")
                ],
                temperature="正常",
                overall_trend="震荡"
            ),
            sentiment=SentimentData(
                status="偏热",
                temperature=65,
                limit_up=85,
                limit_down=12,
                break_board=5,
                main_net_inflow=25.3
            ),
            sectors=SectorData(
                industry_top=[{"name": "电子", "change_pct": 3.5, "trend": "加热中"}],
                concept_top=[{"name": "人工智能", "change_pct": 4.2, "up_ratio": 0.8}],
                fund_flow_top=[{"name": "电子", "net_inflow": 50.0}]
            ),
            northbound=NorthboundData(
                total_flow=44.0,
                status="流入",
                sh_flow=25.3,
                sz_flow=18.7,
                top_inflow=[{"name": "贵州茅台", "hold_change": 85000}],
                top_outflow=[{"name": "中国平安", "hold_change": -32000}]
            ),
            conclusion=Conclusion(
                summary="指数震荡，情绪偏热",
                highlights=["热门行业：电子"],
                risks=["过热预警"]
            )
        )

        result = processor.format_report(report)

        # 检查各部分是否存在
        assert "## 一、市场概览" in result
        assert "## 二、情绪分析" in result
        assert "## 三、板块热点" in result
        assert "## 四、外资动向" in result
        assert "## 五、综合结论" in result
        assert "涨停：85 家" in result
        assert "**北向资金**：流入 (+44.0 亿)" in result
