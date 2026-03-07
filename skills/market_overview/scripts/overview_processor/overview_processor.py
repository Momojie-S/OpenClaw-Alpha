# -*- coding: utf-8 -*-
"""市场综合分析 Processor - 一键式市场分析报告"""

import argparse
import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from openclaw_alpha.core.processor_utils import get_output_path, load_output

logger = logging.getLogger(__name__)

SKILL_NAME = "market_overview"
PROCESSOR_NAME = "overview"


@dataclass
class IndexData:
    """指数数据"""
    name: str
    code: str
    close: float
    change_pct: float
    trend: str


@dataclass
class MacroData:
    """宏观层数据"""
    date: str
    indices: list[IndexData] = field(default_factory=list)
    temperature: str = "未知"
    temperature_score: int = 0
    overall_trend: str = "未知"
    strongest: Optional[dict] = None
    weakest: Optional[dict] = None


@dataclass
class SentimentData:
    """情绪数据"""
    status: str = "未知"
    temperature: int = 0
    limit_up: int = 0
    limit_down: int = 0
    break_board: int = 0
    up_count: int = 0
    down_count: int = 0
    main_net_inflow: float = 0.0
    signals: list[str] = field(default_factory=list)


@dataclass
class SectorData:
    """板块数据"""
    industry_top: list[dict] = field(default_factory=list)
    concept_top: list[dict] = field(default_factory=list)
    fund_flow_top: list[dict] = field(default_factory=list)


@dataclass
class NorthboundData:
    """外资数据"""
    total_flow: float = 0.0
    status: str = "未知"
    sh_flow: float = 0.0
    sz_flow: float = 0.0
    top_inflow: list[dict] = field(default_factory=list)
    top_outflow: list[dict] = field(default_factory=list)


@dataclass
class Conclusion:
    """综合结论"""
    summary: str = ""
    highlights: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)


@dataclass
class OverviewReport:
    """综合分析报告"""
    date: str
    mode: str
    generated_at: str
    overall: dict
    macro: Optional[MacroData] = None
    sentiment: Optional[SentimentData] = None
    sectors: Optional[SectorData] = None
    northbound: Optional[NorthboundData] = None
    conclusion: Optional[Conclusion] = None
    errors: list[str] = field(default_factory=list)


class MarketOverviewProcessor:
    """市场综合分析 Processor"""

    def __init__(self, date: Optional[str] = None, mode: str = "full"):
        """
        初始化

        Args:
            date: 分析日期（YYYY-MM-DD），默认今天
            mode: 分析模式（quick/full）
        """
        self.date = date or datetime.now().strftime("%Y-%m-%d")
        self.mode = mode
        self.errors: list[str] = []

    async def process(self) -> OverviewReport:
        """
        主入口：生成综合报告

        Returns:
            综合分析报告
        """
        report = OverviewReport(
            date=self.date,
            mode=self.mode,
            generated_at=datetime.now().isoformat(),
            overall={"judgment": "未知", "confidence": 0.0}
        )

        # 加载各层数据
        if self.mode in ["quick", "full"]:
            report.macro = await self._load_macro_data()
            report.sentiment = await self._load_sentiment_data()

        if self.mode == "full":
            report.sectors = await self._load_sector_data()
            report.northbound = await self._load_northbound_data()

        # 生成综合判断
        report.overall = self._generate_judgment(report)

        # 生成结论
        report.conclusion = self._generate_conclusion(report)

        # 记录错误
        report.errors = self.errors

        return report

    async def _load_macro_data(self) -> Optional[MacroData]:
        """加载宏观层数据（index_analysis）"""
        try:
            data = load_output("index_analysis", "index", self.date, ext="json")
            if not data:
                self.errors.append("index_analysis: 数据不存在")
                return None

            indices = [
                IndexData(
                    name=i.get("name", ""),
                    code=i.get("code", ""),
                    close=i.get("close", 0.0),
                    change_pct=i.get("change_pct", 0.0),
                    trend=i.get("trend", "未知")
                )
                for i in data.get("indices", [])
            ]

            return MacroData(
                date=data.get("date", self.date),
                indices=indices,
                temperature=data.get("market_temperature", "未知"),
                temperature_score=self._parse_temperature(data.get("market_temperature", "未知")),
                overall_trend=data.get("overall_trend", "未知"),
                strongest=data.get("strongest"),
                weakest=data.get("weakest")
            )
        except Exception as e:
            self.errors.append(f"index_analysis: {str(e)}")
            logger.error(f"加载宏观数据失败: {e}")
            return None

    async def _load_sentiment_data(self) -> Optional[SentimentData]:
        """加载情绪数据（market_sentiment）"""
        try:
            data = load_output("market_sentiment", "sentiment", self.date, ext="json")
            if not data:
                self.errors.append("market_sentiment: 数据不存在")
                return None

            return SentimentData(
                status=data.get("status", "未知"),
                temperature=data.get("temperature", 0),
                limit_up=data.get("limit", {}).get("up", 0),
                limit_down=data.get("limit", {}).get("down", 0),
                break_board=data.get("limit", {}).get("break_board", 0),
                up_count=data.get("trend", {}).get("up", 0),
                down_count=data.get("trend", {}).get("down", 0),
                main_net_inflow=data.get("flow", {}).get("main_net_inflow", 0.0),
                signals=data.get("signals", [])
            )
        except Exception as e:
            self.errors.append(f"market_sentiment: {str(e)}")
            logger.error(f"加载情绪数据失败: {e}")
            return None

    async def _load_sector_data(self) -> Optional[SectorData]:
        """加载板块数据（industry_trend, fund_flow_analysis）"""
        sector_data = SectorData()

        # 加载行业热度
        try:
            heat_data = load_output("industry_trend", "heat", self.date, ext="json")
            if heat_data:
                # 提取行业 Top
                for board in heat_data.get("boards", [])[:5]:
                    if heat_data.get("category") == "L1":
                        sector_data.industry_top.append({
                            "name": board.get("name", ""),
                            "change_pct": board.get("change_pct", 0.0),
                            "trend": board.get("trend", "稳定")
                        })

                # 如果没有 L1 数据，用 concept 数据
                if not sector_data.industry_top and heat_data.get("category") == "concept":
                    sector_data.concept_top = [
                        {
                            "name": b.get("name", ""),
                            "change_pct": b.get("change_pct", 0.0),
                            "up_ratio": b.get("up_ratio", 0.0)
                        }
                        for b in heat_data.get("boards", [])[:5]
                    ]
        except Exception as e:
            self.errors.append(f"industry_trend: {str(e)}")
            logger.error(f"加载板块热度数据失败: {e}")

        # 加载资金流向
        try:
            flow_data = load_output("fund_flow_analysis", "fund_flow", self.date, ext="json")
            if flow_data:
                sector_data.fund_flow_top = [
                    {
                        "name": b.get("name", ""),
                        "net_inflow": b.get("net_inflow", 0.0),
                        "change_pct": b.get("change_pct", 0.0)
                    }
                    for b in flow_data.get("boards", [])[:5]
                ]
        except Exception as e:
            self.errors.append(f"fund_flow_analysis: {str(e)}")
            logger.error(f"加载资金流向数据失败: {e}")

        return sector_data

    async def _load_northbound_data(self) -> Optional[NorthboundData]:
        """加载外资数据（northbound_flow）"""
        try:
            data = load_output("northbound_flow", "northbound", self.date, ext="json")
            if not data:
                self.errors.append("northbound_flow: 数据不存在")
                return None

            return NorthboundData(
                total_flow=data.get("total_flow", 0.0),
                status=data.get("status", "未知"),
                sh_flow=data.get("sh_flow", 0.0),
                sz_flow=data.get("sz_flow", 0.0),
                top_inflow=data.get("top_inflow", [])[:5],
                top_outflow=data.get("top_outflow", [])[:5]
            )
        except Exception as e:
            self.errors.append(f"northbound_flow: {str(e)}")
            logger.error(f"加载外资数据失败: {e}")
            return None

    def _parse_temperature(self, temp_str: str) -> int:
        """解析温度字符串为分数"""
        mapping = {
            "过热": 90,
            "温热": 70,
            "正常": 50,
            "偏冷": 30,
            "过冷": 10
        }
        return mapping.get(temp_str, 50)

    def _generate_judgment(self, report: OverviewReport) -> dict:
        """
        生成综合判断

        Returns:
            judgment: 判断结论
            confidence: 置信度
        """
        # 计算指数平均涨跌幅
        avg_change = 0.0
        if report.macro and report.macro.indices:
            changes = [i.change_pct for i in report.macro.indices]
            avg_change = sum(changes) / len(changes) if changes else 0.0

        # 获取情绪温度
        temp = report.sentiment.temperature if report.sentiment else 50

        # 获取外资流向
        flow = report.northbound.total_flow if report.northbound else 0.0

        # 综合判断
        judgment = "震荡"
        confidence = 0.5

        if avg_change > 1 and temp > 60 and flow > 10:
            judgment = "强势上涨"
            confidence = 0.85
        elif avg_change > 0 and temp > 40:
            judgment = "震荡上涨"
            confidence = 0.70
        elif avg_change < -1 and temp < 40 and flow < -10:
            judgment = "弱势下跌"
            confidence = 0.85
        elif avg_change < 0 and temp < 60:
            judgment = "震荡下跌"
            confidence = 0.70
        else:
            judgment = "震荡"
            confidence = 0.60

        return {
            "judgment": judgment,
            "confidence": confidence,
            "avg_change": round(avg_change, 2),
            "temperature": temp,
            "northbound_flow": flow
        }

    def _generate_conclusion(self, report: OverviewReport) -> Conclusion:
        """生成综合结论"""
        highlights = []
        risks = []
        summary_parts = []

        # 指数分析
        if report.macro:
            trend = report.macro.overall_trend
            summary_parts.append(f"指数{trend}")
            if report.macro.strongest:
                highlights.append(f"最强指数：{report.macro.strongest.get('name', '')} ({report.macro.strongest.get('change_pct', 0):+.1f}%)")

        # 情绪分析
        if report.sentiment:
            status = report.sentiment.status
            limit_up = report.sentiment.limit_up
            summary_parts.append(f"情绪{status}")
            if limit_up > 100:
                highlights.append(f"涨停{limit_up}家，市场活跃")
            if report.sentiment.signals:
                risks.extend(report.sentiment.signals[:2])

        # 板块分析
        if report.sectors:
            if report.sectors.industry_top:
                top = report.sectors.industry_top[0]
                highlights.append(f"热门行业：{top['name']} ({top['change_pct']:+.1f}%)")
            if report.sectors.concept_top:
                concepts = [c['name'] for c in report.sectors.concept_top[:3]]
                highlights.append(f"热门概念：{', '.join(concepts)}")

        # 外资分析
        if report.northbound:
            flow = report.northbound.total_flow
            status = report.northbound.status
            summary_parts.append(f"外资{status}")
            if flow > 0:
                highlights.append(f"北向资金流入 {flow:.1f} 亿")
            elif flow < 0:
                risks.append(f"北向资金流出 {abs(flow):.1f} 亿")

        summary = "，".join(summary_parts) if summary_parts else "数据不足，无法生成结论"

        return Conclusion(
            summary=summary,
            highlights=highlights[:5],
            risks=risks[:3]
        )

    def format_report(self, report: OverviewReport) -> str:
        """
        格式化 Markdown 报告

        Args:
            report: 综合分析报告

        Returns:
            Markdown 格式的报告文本
        """
        lines = []
        lines.append(f"# 市场分析报告 - {report.date}")
        lines.append("")
        lines.append(f"**分析模式**：{'快速版' if report.mode == 'quick' else '完整版'}")
        lines.append(f"**生成时间**：{report.generated_at}")
        lines.append("")

        # 综合判断
        lines.append("## 综合判断")
        lines.append("")
        lines.append(f"**{report.overall['judgment']}** (置信度: {report.overall['confidence']*100:.0f}%)")
        lines.append("")

        # 一、市场概览
        if report.macro:
            lines.append("## 一、市场概览")
            lines.append("")
            lines.append(f"**市场温度**：{report.macro.temperature}")
            lines.append(f"**整体趋势**：{report.macro.overall_trend}")
            lines.append("")

            if report.macro.indices:
                lines.append("| 指数 | 收盘 | 涨跌幅 | 趋势 |")
                lines.append("|------|------|--------|------|")
                for idx in report.macro.indices[:6]:
                    change_str = f"{idx.change_pct:+.2f}%"
                    lines.append(f"| {idx.name} | {idx.close:.2f} | {change_str} | {idx.trend} |")
                lines.append("")

        # 二、情绪分析
        if report.sentiment:
            lines.append("## 二、情绪分析")
            lines.append("")
            lines.append(f"**情绪状态**：{report.sentiment.status} (温度: {report.sentiment.temperature})")
            lines.append("")
            lines.append(f"- 涨停：{report.sentiment.limit_up} 家")
            lines.append(f"- 跌停：{report.sentiment.limit_down} 家")
            lines.append(f"- 炸板：{report.sentiment.break_board} 家")
            lines.append(f"- 主力净流入：{report.sentiment.main_net_inflow:+.1f} 亿")
            lines.append("")

            if report.sentiment.signals:
                lines.append("**极端信号**：")
                for sig in report.sentiment.signals:
                    lines.append(f"- {sig}")
                lines.append("")

        # 三、板块热点（仅完整版）
        if report.mode == "full" and report.sectors:
            lines.append("## 三、板块热点")
            lines.append("")

            if report.sectors.industry_top:
                lines.append("**行业 Top 5**：")
                for i, s in enumerate(report.sectors.industry_top, 1):
                    lines.append(f"{i}. {s['name']} ({s['change_pct']:+.1f}%) - {s['trend']}")
                lines.append("")

            if report.sectors.concept_top:
                lines.append("**概念 Top 5**：")
                for i, s in enumerate(report.sectors.concept_top, 1):
                    up_ratio = s.get('up_ratio', 0)
                    lines.append(f"{i}. {s['name']} ({s['change_pct']:+.1f}%) - 涨家比 {up_ratio:.0%}")
                lines.append("")

            if report.sectors.fund_flow_top:
                lines.append("**资金流入 Top 5**：")
                for i, s in enumerate(report.sectors.fund_flow_top, 1):
                    lines.append(f"{i}. {s['name']} (净流入 {s['net_inflow']:+.1f} 亿)")
                lines.append("")

        # 四、外资动向（仅完整版）
        if report.mode == "full" and report.northbound:
            lines.append("## 四、外资动向")
            lines.append("")
            lines.append(f"**北向资金**：{report.northbound.status} ({report.northbound.total_flow:+.1f} 亿)")
            lines.append(f"- 沪股通：{report.northbound.sh_flow:+.1f} 亿")
            lines.append(f"- 深股通：{report.northbound.sz_flow:+.1f} 亿")
            lines.append("")

            if report.northbound.top_inflow:
                lines.append("**买入 Top 5**：")
                for s in report.northbound.top_inflow[:5]:
                    change = s.get('hold_change', 0)
                    lines.append(f"- {s.get('name', '')} ({change/10000:+.2f} 亿)")
                lines.append("")

        # 五、综合结论
        if report.conclusion:
            lines.append("## 五、综合结论")
            lines.append("")
            lines.append(report.conclusion.summary)
            lines.append("")

            if report.conclusion.highlights:
                lines.append("**关注点**：")
                for h in report.conclusion.highlights:
                    lines.append(f"- {h}")
                lines.append("")

            if report.conclusion.risks:
                lines.append("**风险提示**：")
                for r in report.conclusion.risks:
                    lines.append(f"- {r}")
                lines.append("")

        # 错误信息
        if report.errors:
            lines.append("## 数据获取问题")
            lines.append("")
            for err in report.errors:
                lines.append(f"- {err}")
            lines.append("")

        return "\n".join(lines)


async def process(date: Optional[str] = None, mode: str = "full") -> OverviewReport:
    """
    生成市场综合分析报告

    Args:
        date: 分析日期
        mode: 分析模式（quick/full）

    Returns:
        综合分析报告
    """
    processor = MarketOverviewProcessor(date=date, mode=mode)
    return await processor.process()


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="市场综合分析报告")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                        help="分析日期 (YYYY-MM-DD)")
    parser.add_argument("--mode", choices=["quick", "full"], default="full",
                        help="分析模式: quick(快速) / full(完整)")
    parser.add_argument("--output", choices=["text", "json"], default="text",
                        help="输出格式: text(Markdown) / json")
    args = parser.parse_args()

    # 生成报告
    report = asyncio.run(process(date=args.date, mode=args.mode))

    # 保存 JSON 文件
    output_path = get_output_path(SKILL_NAME, PROCESSOR_NAME, args.date, ext="json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 转换为可序列化的字典
    report_dict = {
        "date": report.date,
        "mode": report.mode,
        "generated_at": report.generated_at,
        "overall": report.overall,
        "macro": asdict(report.macro) if report.macro else None,
        "sentiment": asdict(report.sentiment) if report.sentiment else None,
        "sectors": asdict(report.sectors) if report.sectors else None,
        "northbound": asdict(report.northbound) if report.northbound else None,
        "conclusion": asdict(report.conclusion) if report.conclusion else None,
        "errors": report.errors
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, ensure_ascii=False, indent=2)

    # 输出
    if args.output == "json":
        print(json.dumps(report_dict, ensure_ascii=False, indent=2))
    else:
        processor = MarketOverviewProcessor(date=args.date, mode=args.mode)
        print(processor.format_report(report))

    print(f"\n[报告已保存] {output_path}")


if __name__ == "__main__":
    main()
