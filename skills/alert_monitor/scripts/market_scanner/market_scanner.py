# -*- coding: utf-8 -*-
"""市场异动扫描器"""

import argparse
import asyncio
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

from skills.alert_monitor.scripts.config_parser import (
    AlertConfig,
    load_config,
)


@dataclass
class MarketSignal:
    """市场信号"""
    type: str  # 北向流入、北向流出、板块热度上升、板块热度下降
    level: str  # 高、中、低
    detail: str
    data: dict = field(default_factory=dict)


@dataclass
class MarketScanResult:
    """市场扫描结果"""
    date: str
    signals: list[MarketSignal] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "signals": [asdict(s) for s in self.signals],
        }


async def scan_northbound_flow(
    config: AlertConfig,
    date: str,
) -> list[MarketSignal]:
    """扫描北向资金异动

    Args:
        config: 预警配置
        date: 检查日期

    Returns:
        异动信号列表
    """
    if not config.northbound_flow.enabled:
        return []

    signals = []

    try:
        # 导入 northbound_flow skill
        from skills.northbound_flow.scripts.flow_fetcher import fetch_daily

        data = await fetch_daily(date)

        if not data:
            return []

        # fetch_daily 返回的 total_flow 是净流入（亿）
        net_amount = data.get("total_flow", 0)  # 亿

        # 检查大额流入
        if net_amount >= config.northbound_flow.inflow_threshold:
            signals.append(MarketSignal(
                type="北向大幅流入",
                level="中",
                detail=f"今日净流入 {net_amount:.1f} 亿",
                data=data,
            ))

        # 检查大额流出
        if net_amount <= -config.northbound_flow.outflow_threshold:
            signals.append(MarketSignal(
                type="北向大幅流出",
                level="高",
                detail=f"今日净流出 {-net_amount:.1f} 亿",
                data=data,
            ))

    except Exception as e:
        signals.append(MarketSignal(
            type="北向资金扫描失败",
            level="低",
            detail=str(e),
        ))

    return signals


async def scan_industry_trend(
    config: AlertConfig,
    date: str,
) -> list[MarketSignal]:
    """扫描板块热度变化

    Args:
        config: 预警配置
        date: 检查日期

    Returns:
        异动信号列表
    """
    if not config.industry_trend.enabled:
        return []

    signals = []

    try:
        # 导入 industry_trend skill
        from skills.industry_trend.scripts.industry_trend_processor.industry_trend_processor import (
            IndustryTrendProcessor,
        )

        processor = IndustryTrendProcessor()
        result = await processor.process(category="L1", date=date, top_n=20)

        boards = result.get("boards", [])
        
        if not boards:
            return []

        # 检查热度大幅变化
        for board in boards:
            change = board.get("heat_change")
            
            # 跳过无历史数据的板块
            if change is None:
                continue

            if change >= config.industry_trend.hot_threshold:
                signals.append(MarketSignal(
                    type="板块热度急升",
                    level="中",
                    detail=f"{board.get('name', '')}: 热度环比 +{change:.1f}%",
                    data={"board": board.get("name"), "change": change},
                ))
            elif change <= config.industry_trend.cold_threshold:
                signals.append(MarketSignal(
                    type="板块热度骤降",
                    level="中",
                    detail=f"{board.get('name', '')}: 热度环比 {change:.1f}%",
                    data={"board": board.get("name"), "change": change},
                ))

    except Exception as e:
        signals.append(MarketSignal(
            type="板块热度扫描失败",
            level="低",
            detail=str(e),
        ))

    return signals


async def scan_market_anomalies(
    date: str,
    config: Optional[AlertConfig] = None,
) -> MarketScanResult:
    """扫描市场异动

    Args:
        date: 检查日期
        config: 预警配置

    Returns:
        MarketScanResult
    """
    if config is None:
        config = load_config()

    result = MarketScanResult(date=date)

    # 并行扫描北向资金和板块热度
    northbound_task = scan_northbound_flow(config, date)
    industry_task = scan_industry_trend(config, date)

    northbound_signals, industry_signals = await asyncio.gather(
        northbound_task, industry_task
    )

    result.signals.extend(northbound_signals)
    result.signals.extend(industry_signals)

    return result


def format_market_report(result: MarketScanResult) -> str:
    """格式化市场扫描报告

    Args:
        result: 市场扫描结果

    Returns:
        格式化的文本报告
    """
    lines = [
        "=" * 60,
        f"市场异动扫描报告 - {result.date}",
        "=" * 60,
    ]

    if not result.signals:
        lines.append("")
        lines.append("无明显市场异动")
        return "\n".join(lines)

    # 按类型分组
    high_signals = [s for s in result.signals if s.level == "高"]
    medium_signals = [s for s in result.signals if s.level == "中"]

    if high_signals:
        lines.extend(["", "【高风险信号】", ""])
        for signal in high_signals:
            lines.append(f"  🔴 {signal.type}")
            lines.append(f"      {signal.detail}")

    if medium_signals:
        lines.extend(["", "【中风险信号】", ""])
        for signal in medium_signals:
            lines.append(f"  🟡 {signal.type}")
            lines.append(f"      {signal.detail}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="市场异动扫描")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--output", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    result = asyncio.run(scan_market_anomalies(args.date))

    if args.output:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(format_market_report(result))


if __name__ == "__main__":
    main()
