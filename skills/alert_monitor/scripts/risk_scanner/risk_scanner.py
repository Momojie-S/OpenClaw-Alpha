# -*- coding: utf-8 -*-
"""持仓风险扫描器"""

import argparse
import asyncio
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

from skills.alert_monitor.scripts.config_parser import (
    AlertConfig,
    load_config,
    get_watchlist_symbols,
)


@dataclass
class RiskSignal:
    """风险信号"""
    type: str  # 业绩风险、价格风险、资金风险、解禁风险
    level: str  # 高、中、低
    detail: str
    suggestion: Optional[str] = None


@dataclass
class StockRiskReport:
    """单只股票风险报告"""
    symbol: str
    name: str
    rating: str  # 高风险、中风险、低风险、正常
    signals: list[RiskSignal] = field(default_factory=list)


@dataclass
class RiskScanResult:
    """风险扫描结果"""
    date: str
    total: int
    high_risk: list[StockRiskReport] = field(default_factory=list)
    medium_risk: list[StockRiskReport] = field(default_factory=list)
    low_risk: list[StockRiskReport] = field(default_factory=list)
    normal: list[StockRiskReport] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "total": self.total,
            "summary": {
                "high_risk": len(self.high_risk),
                "medium_risk": len(self.medium_risk),
                "low_risk": len(self.low_risk),
                "normal": len(self.normal),
            },
            "high_risk": [asdict(r) for r in self.high_risk],
            "medium_risk": [asdict(r) for r in self.medium_risk],
            "low_risk": [asdict(r) for r in self.low_risk],
            "normal": [asdict(r) for r in self.normal],
        }


async def scan_stock_risk(symbol: str, date: str, days: int = 5) -> StockRiskReport:
    """扫描单只股票的风险

    复用 risk_alert skill 的逻辑，但返回更精简的结果

    Args:
        symbol: 股票代码
        date: 检查日期
        days: 检查近 N 天

    Returns:
        StockRiskReport
    """
    # 导入 risk_alert 的 processor
    from skills.risk_alert.scripts.risk_processor.risk_processor import check_stock_risk

    result = await check_stock_risk(symbol, date, days)

    signals = []
    for risk in result.get("risks", []):
        signals.append(RiskSignal(
            type=risk.get("type", "未知"),
            level=risk.get("level", "低"),
            detail=risk.get("detail", ""),
            suggestion=risk.get("suggestion"),
        ))

    return StockRiskReport(
        symbol=symbol,
        name=result.get("name", ""),
        rating=result.get("rating", "正常"),
        signals=signals,
    )


async def scan_portfolio_risk(
    symbols: list[str],
    date: str,
    days: int = 5,
    config: Optional[AlertConfig] = None,
) -> RiskScanResult:
    """扫描持仓风险

    Args:
        symbols: 股票代码列表
        date: 检查日期
        days: 检查近 N 天
        config: 预警配置

    Returns:
        RiskScanResult
    """
    if config is None:
        config = load_config()

    # 检查是否启用风险预警
    if not config.risk_alert.enabled:
        return RiskScanResult(date=date, total=0)

    result = RiskScanResult(date=date, total=len(symbols))

    for symbol in symbols:
        try:
            report = await scan_stock_risk(symbol, date, days)

            if report.rating == "高风险":
                result.high_risk.append(report)
            elif report.rating == "中风险":
                result.medium_risk.append(report)
            elif report.rating == "低风险":
                result.low_risk.append(report)
            else:
                result.normal.append(report)
        except Exception as e:
            # 扫描失败，记录为正常
            result.normal.append(StockRiskReport(
                symbol=symbol,
                name="",
                rating="正常",
                signals=[RiskSignal(
                    type="扫描失败",
                    level="低",
                    detail=str(e),
                )],
            ))

    return result


def format_risk_report(result: RiskScanResult) -> str:
    """格式化风险报告为可读文本

    Args:
        result: 风险扫描结果

    Returns:
        格式化的文本报告
    """
    lines = [
        "=" * 60,
        f"持仓风险扫描报告 - {result.date}",
        "=" * 60,
        "",
        f"扫描股票: {result.total} 只",
        "",
        "【汇总统计】",
        f"  高风险: {len(result.high_risk)} 只",
        f"  中风险: {len(result.medium_risk)} 只",
        f"  低风险: {len(result.low_risk)} 只",
        f"  正常: {len(result.normal)} 只",
    ]

    if result.high_risk:
        lines.extend(["", "【高风险】", ""])
        for report in result.high_risk:
            signals_text = " | ".join([f"{s.type}: {s.detail}" for s in report.signals])
            lines.append(f"  ⚠️ {report.symbol} {report.name}: {signals_text}")

    if result.medium_risk:
        lines.extend(["", "【中风险】", ""])
        for report in result.medium_risk:
            signals_text = " | ".join([f"{s.type}: {s.detail}" for s in report.signals])
            lines.append(f"  ⚡ {report.symbol} {report.name}: {signals_text}")

    if result.low_risk:
        lines.extend(["", "【低风险】", ""])
        for report in result.low_risk:
            signals_text = " | ".join([f"{s.type}: {s.detail}" for s in report.signals])
            lines.append(f"  ℹ️ {report.symbol} {report.name}: {signals_text}")

    if result.high_risk or result.medium_risk:
        lines.extend(["", "【建议】"])
        if result.high_risk:
            lines.append(f"  请优先处理 {len(result.high_risk)} 只高风险股票")
        if result.medium_risk:
            lines.append(f"  密切关注 {len(result.medium_risk)} 只中风险股票")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="持仓风险扫描")
    parser.add_argument("--symbols", help="股票代码（逗号分隔）")
    parser.add_argument("--watchlist", action="store_true", help="从配置读取自选股")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--days", type=int, default=5)
    parser.add_argument("--output", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    if args.watchlist:
        config = load_config()
        symbols = get_watchlist_symbols(config)
    elif args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]
    else:
        print("请指定 --symbols 或 --watchlist")
        return

    result = asyncio.run(scan_portfolio_risk(symbols, args.date, args.days))

    if args.output:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(format_risk_report(result))


if __name__ == "__main__":
    main()
