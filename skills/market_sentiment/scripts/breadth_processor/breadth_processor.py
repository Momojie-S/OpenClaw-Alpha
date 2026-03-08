# -*- coding: utf-8 -*-
"""市场宽度分析处理器

分析市场宽度指标，判断市场趋势的健康程度。
"""

import argparse
import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..breadth_fetcher import fetch as fetch_breadth, BreadthData
from openclaw_alpha.core.processor_utils import get_output_path


@dataclass
class BreadthAnalysis:
    """市场宽度分析结果"""

    date: str
    close: float

    # 原始数据
    high20: int
    low20: int
    high60: int
    low60: int
    high120: int
    low120: int

    # 计算指标
    breadth_ratio_20: float
    breadth_ratio_60: float
    breadth_ratio_120: float

    # 健康度
    health_level: str
    health_score: float

    # 趋势（需要多日数据）
    trend: Optional[str] = None
    trend_change: Optional[float] = None

    # 信号
    signals: list[str] = None

    def __post_init__(self):
        if self.signals is None:
            self.signals = []


def _calc_health_level(ratio: float) -> tuple[str, float]:
    """
    计算健康度等级

    Args:
        ratio: 宽度比率

    Returns:
        (健康度等级, 健康度分数)
    """
    if ratio >= 0.7:
        return "健康", ratio * 100
    elif ratio >= 0.5:
        return "正常", 50 + (ratio - 0.5) * 100
    elif ratio >= 0.3:
        return "偏弱", ratio * 100
    else:
        return "危险", ratio * 50


def _calc_trend(data_list: list[BreadthData]) -> tuple[Optional[str], Optional[float]]:
    """
    计算宽度趋势

    Args:
        data_list: 多日数据（按日期降序）

    Returns:
        (趋势, 变化值)
    """
    if len(data_list) < 5:
        return None, None

    # 计算最近5日和前5日的平均宽度比率
    recent_5 = sum(d.breadth_ratio_20 for d in data_list[:5]) / 5
    prev_5 = sum(d.breadth_ratio_20 for d in data_list[5:10]) / 5

    change = recent_5 - prev_5

    if change > 0.1:
        return "上升", change
    elif change < -0.1:
        return "下降", change
    else:
        return "平稳", change


def _detect_signals(
    current: BreadthData, data_list: list[BreadthData]
) -> list[str]:
    """
    检测市场宽度信号

    Args:
        current: 当前数据
        data_list: 多日数据

    Returns:
        信号列表
    """
    signals = []

    # 健康度信号
    ratio = current.breadth_ratio_20
    if ratio >= 0.8:
        signals.append("市场宽度极度健康，大部分股票走强")
    elif ratio <= 0.2:
        signals.append("市场宽度极度危险，大部分股票走弱")

    # 背离信号
    if len(data_list) >= 5:
        prev = data_list[4]  # 5个交易日前

        # 顶背离：指数上涨但宽度下降
        if current.close > prev.close and current.breadth_ratio_20 < prev.breadth_ratio_20 - 0.1:
            signals.append("顶背离信号：指数上涨但市场宽度收窄，注意风险")

        # 底背离：指数下跌但宽度上升
        if current.close < prev.close and current.breadth_ratio_20 > prev.breadth_ratio_20 + 0.1:
            signals.append("底背离信号：指数下跌但市场宽度改善，关注机会")

    # 新高新低极端值
    if current.high20 > current.low20 * 3:
        signals.append(f"20日新高股数({current.high20})远超新低({current.low20})")
    elif current.low20 > current.high20 * 3:
        signals.append(f"20日新低股数({current.low20})远超新高({current.high20})")

    return signals


async def process(
    symbol: str = "all",
    days: int = 30,
    output_json: bool = True,
) -> dict:
    """
    分析市场宽度

    Args:
        symbol: 指数类型 (all/sz50/hs300/zz500)
        days: 分析天数
        output_json: 是否保存 JSON 文件

    Returns:
        分析结果字典
    """
    # 获取数据
    data_list = await fetch_breadth(symbol=symbol, days=days)

    if not data_list:
        return {"error": "无法获取市场宽度数据"}

    # 当前数据
    current = data_list[0]

    # 计算健康度
    health_level, health_score = _calc_health_level(current.breadth_ratio_20)

    # 计算趋势
    trend, trend_change = _calc_trend(data_list)

    # 检测信号
    signals = _detect_signals(current, data_list)

    # 构建分析结果
    analysis = BreadthAnalysis(
        date=current.date,
        close=current.close,
        high20=current.high20,
        low20=current.low20,
        high60=current.high60,
        low60=current.low60,
        high120=current.high120,
        low120=current.low120,
        breadth_ratio_20=current.breadth_ratio_20,
        breadth_ratio_60=current.breadth_ratio_60,
        breadth_ratio_120=current.breadth_ratio_120,
        health_level=health_level,
        health_score=health_score,
        trend=trend,
        trend_change=trend_change,
        signals=signals,
    )

    # 构建输出
    result = {
        "date": analysis.date,
        "close": analysis.close,
        "breadth": {
            "ratio_20": round(analysis.breadth_ratio_20, 4),
            "ratio_60": round(analysis.breadth_ratio_60, 4),
            "ratio_120": round(analysis.breadth_ratio_120, 4),
        },
        "statistics": {
            "high20": analysis.high20,
            "low20": analysis.low20,
            "high60": analysis.high60,
            "low60": analysis.low60,
            "high120": analysis.high120,
            "low120": analysis.low120,
        },
        "health": {
            "level": analysis.health_level,
            "score": round(analysis.health_score, 1),
        },
        "trend": {
            "direction": analysis.trend,
            "change": round(analysis.trend_change, 4) if analysis.trend_change else None,
        },
        "signals": analysis.signals,
    }

    # 添加历史数据
    if len(data_list) > 1:
        result["history"] = [
            {
                "date": d.date,
                "close": d.close,
                "breadth_ratio_20": round(d.breadth_ratio_20, 4),
            }
            for d in data_list[:10]  # 最近10天
        ]

    # 保存文件
    if output_json:
        output_path = get_output_path(
            skill_name="market_sentiment",
            processor_name="breadth",
            date=datetime.now().strftime("%Y-%m-%d"),
            ext="json",
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def _format_report(result: dict) -> str:
    """格式化输出报告"""
    lines = []
    lines.append("=" * 50)
    lines.append("市场宽度分析报告")
    lines.append("=" * 50)
    lines.append(f"日期: {result['date']}")
    lines.append(f"收盘点位: {result['close']:.2f}")
    lines.append("")

    # 宽度指标
    lines.append("【宽度指标】")
    breadth = result["breadth"]
    lines.append(f"  20日宽度比率: {breadth['ratio_20']:.1%}")
    lines.append(f"  60日宽度比率: {breadth['ratio_60']:.1%}")
    lines.append(f"  120日宽度比率: {breadth['ratio_120']:.1%}")
    lines.append("")

    # 统计数据
    lines.append("【新高新低统计】")
    stats = result["statistics"]
    lines.append(f"  20日: 新高 {stats['high20']} / 新低 {stats['low20']}")
    lines.append(f"  60日: 新高 {stats['high60']} / 新低 {stats['low60']}")
    lines.append(f"  120日: 新高 {stats['high120']} / 新低 {stats['low120']}")
    lines.append("")

    # 健康度
    lines.append("【健康度评估】")
    health = result["health"]
    lines.append(f"  等级: {health['level']}")
    lines.append(f"  得分: {health['score']:.1f}")
    lines.append("")

    # 趋势
    trend = result.get("trend", {})
    if trend.get("direction"):
        lines.append("【趋势分析】")
        lines.append(f"  方向: {trend['direction']}")
        if trend["change"] is not None:
            lines.append(f"  变化: {trend['change']:+.1%}")
        lines.append("")

    # 信号
    signals = result.get("signals", [])
    if signals:
        lines.append("【市场信号】")
        for sig in signals:
            lines.append(f"  ⚠️ {sig}")
        lines.append("")

    lines.append("=" * 50)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="市场宽度分析")
    parser.add_argument(
        "--symbol",
        default="all",
        choices=["all", "sz50", "hs300", "zz500"],
        help="指数类型",
    )
    parser.add_argument("--days", type=int, default=30, help="分析天数")
    parser.add_argument("--output", choices=["text", "json"], default="text", help="输出格式")

    args = parser.parse_args()

    result = asyncio.run(process(symbol=args.symbol, days=args.days))

    if "error" in result:
        print(f"错误: {result['error']}")
        return

    if args.output == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_format_report(result))


if __name__ == "__main__":
    main()
