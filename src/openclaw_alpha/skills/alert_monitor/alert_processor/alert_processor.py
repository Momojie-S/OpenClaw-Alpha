# -*- coding: utf-8 -*-
"""综合预警扫描处理器"""

import argparse
import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from openclaw_alpha.core.processor_utils import get_output_path

from openclaw_alpha.skills.alert_monitor.config_parser import (
    AlertConfig,
    load_config,
    get_watchlist_symbols,
)
from openclaw_alpha.skills.alert_monitor.risk_scanner import scan_portfolio_risk
from openclaw_alpha.skills.alert_monitor.market_scanner import scan_market_anomalies


@dataclass
class AlertReport:
    """综合预警报告"""
    date: str
    scan_type: str  # full, risk, market
    risk_result: Optional[dict] = None
    market_result: Optional[dict] = None
    has_high_risk: bool = False
    has_anomaly: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


async def run_full_scan(
    config: AlertConfig,
    date: str,
    days: int = 5,
) -> AlertReport:
    """运行综合扫描

    Args:
        config: 预警配置
        date: 扫描日期
        days: 检查近 N 天

    Returns:
        AlertReport
    """
    report = AlertReport(
        date=date,
        scan_type="full",
    )

    # 1. 持仓风险扫描
    if config.watchlist:
        symbols = get_watchlist_symbols(config)
        risk_result = await scan_portfolio_risk(symbols, date, days, config)
        report.risk_result = risk_result.to_dict()
        report.has_high_risk = len(risk_result.high_risk) > 0

    # 2. 市场异动扫描
    market_result = await scan_market_anomalies(date, config)
    report.market_result = market_result.to_dict()
    report.has_anomaly = len(market_result.signals) > 0

    return report


async def run_risk_scan(
    config: AlertConfig,
    date: str,
    days: int = 5,
) -> AlertReport:
    """仅运行风险扫描

    Args:
        config: 预警配置
        date: 扫描日期
        days: 检查近 N 天

    Returns:
        AlertReport
    """
    report = AlertReport(
        date=date,
        scan_type="risk",
    )

    if config.watchlist:
        symbols = get_watchlist_symbols(config)
        risk_result = await scan_portfolio_risk(symbols, date, days, config)
        report.risk_result = risk_result.to_dict()
        report.has_high_risk = len(risk_result.high_risk) > 0

    return report


async def run_market_scan(
    config: AlertConfig,
    date: str,
) -> AlertReport:
    """仅运行市场扫描

    Args:
        config: 预警配置
        date: 扫描日期

    Returns:
        AlertReport
    """
    report = AlertReport(
        date=date,
        scan_type="market",
    )

    market_result = await scan_market_anomalies(date, config)
    report.market_result = market_result.to_dict()
    report.has_anomaly = len(market_result.signals) > 0

    return report


def format_alert_report(report: AlertReport, brief: bool = False) -> str:
    """格式化预警报告

    Args:
        report: 预警报告
        brief: 是否生成简报

    Returns:
        格式化的文本报告
    """
    lines = [
        "📊 【预警扫描报告】" + report.date,
        "",
    ]

    # 持仓风险摘要
    if report.risk_result:
        summary = report.risk_result.get("summary", {})
        high = summary.get("high_risk", 0)
        medium = summary.get("medium_risk", 0)

        lines.append("【持仓风险】")
        lines.append(f"  扫描: {report.risk_result.get('total', 0)} 只")
        lines.append(f"  高风险: {high} 只 | 中风险: {medium} 只")

        # 简报模式：只显示高风险
        if brief and report.risk_result.get("high_risk"):
            lines.append("")
            lines.append("【高风险详情】")
            for item in report.risk_result["high_risk"][:5]:
                signals = " | ".join([s["detail"] for s in item.get("signals", [])])
                lines.append(f"  ⚠️ {item['symbol']} {item['name']}: {signals}")
        elif not brief:
            # 完整报告
            if report.risk_result.get("high_risk"):
                lines.append("")
                lines.append("【高风险】")
                for item in report.risk_result["high_risk"]:
                    signals = " | ".join([s["detail"] for s in item.get("signals", [])])
                    lines.append(f"  ⚠️ {item['symbol']} {item['name']}: {signals}")

            if report.risk_result.get("medium_risk"):
                lines.append("")
                lines.append("【中风险】")
                for item in report.risk_result["medium_risk"]:
                    signals = " | ".join([s["detail"] for s in item.get("signals", [])])
                    lines.append(f"  ⚡ {item['symbol']} {item['name']}: {signals}")

    # 市场异动摘要
    if report.market_result:
        signals = report.market_result.get("signals", [])

        lines.append("")
        lines.append("【市场异动】")

        if not signals:
            lines.append("  无明显异动")
        else:
            # 按类型分组
            high_signals = [s for s in signals if s.get("level") == "高"]
            medium_signals = [s for s in signals if s.get("level") == "中"]

            if high_signals:
                for s in high_signals[:3]:
                    lines.append(f"  🔴 {s['type']}: {s['detail']}")

            if medium_signals:
                for s in medium_signals[:5]:
                    lines.append(f"  🟡 {s['type']}: {s['detail']}")

    # 行动建议
    if report.has_high_risk or report.has_anomaly:
        lines.append("")
        lines.append("【建议】")
        if report.has_high_risk:
            lines.append("  ⚠️ 存在高风险持仓，请及时处理")
        if report.has_anomaly:
            lines.append("  📈 市场出现异动，请关注")

    return "\n".join(lines)


def save_report(report: AlertReport, date: str) -> Path:
    """保存报告到文件

    Args:
        report: 预警报告
        date: 日期

    Returns:
        保存路径
    """
    output_path = get_output_path(
        skill_name="alert_monitor",
        processor_name="alert_processor",
        date=date,
        ext="json",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)

    return output_path


def main():
    parser = argparse.ArgumentParser(description="综合预警扫描")
    parser.add_argument(
        "--type",
        choices=["full", "risk", "market"],
        default="full",
        help="扫描类型：full=综合, risk=仅风险, market=仅市场",
    )
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--days", type=int, default=5, help="检查近 N 天")
    parser.add_argument("--brief", action="store_true", help="简报模式")
    parser.add_argument("--output", action="store_true", help="保存到文件")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    config = load_config()

    if args.type == "full":
        report = asyncio.run(run_full_scan(config, args.date, args.days))
    elif args.type == "risk":
        report = asyncio.run(run_risk_scan(config, args.date, args.days))
    else:
        report = asyncio.run(run_market_scan(config, args.date))

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(format_alert_report(report, brief=args.brief))

    if args.output:
        path = save_report(report, args.date)
        print(f"\n报告已保存: {path}")


if __name__ == "__main__":
    main()
