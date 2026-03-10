# -*- coding: utf-8 -*-
"""北向资金分析 Processor"""

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path

from openclaw_alpha.core.processor_utils import get_output_path
from openclaw_alpha.core.signal_utils import (
    build_signal_id,
    build_signal_data,
    save_signal,
)
from ..flow_fetcher import fetch_daily, fetch_stocks, fetch_trend


# 常量定义
SKILL_NAME = "northbound_flow"
PROCESSOR_NAME = "northbound"

# 北向资金是市场整体指标，用 MARKET 作为 stock_code
MARKET_CODE = "MARKET"


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="北向资金分析")
    parser.add_argument(
        "--action",
        choices=["daily", "stock", "trend", "signals"],
        default="daily",
        help="查询类型：daily（每日净流入）、stock（个股流向）、trend（资金趋势）、signals（信号输出）"
    )
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="查询日期（默认今天）"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="趋势/信号天数（默认 30 天）"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Top N（默认 10）"
    )
    # 信号输出参数
    parser.add_argument(
        "--save-signals",
        action="store_true",
        help="同时输出信号文件"
    )
    parser.add_argument(
        "--signal-only",
        action="store_true",
        help="只输出信号文件（不输出分析结果）"
    )
    # 信号参数
    parser.add_argument(
        "--consecutive",
        type=int,
        default=3,
        help="连续天数阈值（默认 3 天）"
    )
    parser.add_argument(
        "--large-inflow",
        type=float,
        default=50.0,
        help="大幅流入阈值（亿元，默认 50）"
    )
    parser.add_argument(
        "--large-outflow",
        type=float,
        default=50.0,
        help="大幅流出阈值（亿元，默认 50）"
    )
    return parser.parse_args()


async def process_daily(date: str, top_n: int) -> dict:
    """
    处理每日净流入查询

    Args:
        date: 日期（如果无数据则返回最近交易日）
        top_n: Top N（用于个股数据）

    Returns:
        分析结果
    """
    # 获取每日净流入（不指定日期，获取最新）
    daily = await fetch_daily(date=None)

    if not daily:
        return {
            "date": date,
            "error": "无数据"
        }

    # 使用返回的日期获取个股数据
    actual_date = daily["date"]

    # 获取个股流入 Top N
    inflow_stocks = await fetch_stocks(actual_date, "inflow")
    top_inflow = inflow_stocks[:top_n]

    # 获取个股流出 Top N
    outflow_stocks = await fetch_stocks(actual_date, "outflow")
    top_outflow = outflow_stocks[:top_n]

    result = {
        "date": daily["date"],
        "sh_flow": daily["sh_flow"],
        "sz_flow": daily["sz_flow"],
        "total_flow": daily["total_flow"],
        "status": daily["status"],
        "top_inflow": top_inflow,
        "top_outflow": top_outflow
    }

    # 保存完整数据
    output_path = get_output_path(SKILL_NAME, PROCESSOR_NAME, date, ext="json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    # 返回精简结果
    return {
        "date": daily["date"],
        "total_flow": daily["total_flow"],
        "status": daily["status"],
        "top_inflow": [
            {"name": s["name"], "hold_change": s["hold_change"]}
            for s in top_inflow[:3]
        ],
        "top_outflow": [
            {"name": s["name"], "hold_change": s["hold_change"]}
            for s in top_outflow[:3]
        ]
    }


async def process_stock(date: str, top_n: int) -> dict:
    """
    处理个股流向查询

    Args:
        date: 日期
        top_n: Top N

    Returns:
        分析结果
    """
    # 获取个股流入
    inflow_stocks = await fetch_stocks(date, "inflow")
    top_inflow = inflow_stocks[:top_n]

    # 获取个股流出
    outflow_stocks = await fetch_stocks(date, "outflow")
    top_outflow = outflow_stocks[:top_n]

    result = {
        "date": date,
        "top_inflow": top_inflow,
        "top_outflow": top_outflow
    }

    # 保存完整数据
    output_path = get_output_path(SKILL_NAME, f"{PROCESSOR_NAME}_stock", date, ext="json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    return result


async def process_trend(days: int, end_date: str) -> dict:
    """
    处理资金趋势查询

    Args:
        days: 天数
        end_date: 结束日期

    Returns:
        分析结果
    """
    # 获取趋势数据
    trend = await fetch_trend(days, end_date)

    result = {
        "period": trend["period"],
        "total_inflow": trend["total_inflow"],
        "avg_inflow": trend["avg_inflow"],
        "inflow_days": trend["inflow_days"],
        "outflow_days": trend["outflow_days"],
        "trend": trend["trend"],
        "daily_data": trend["daily_data"]
    }

    # 保存完整数据
    output_path = get_output_path(SKILL_NAME, f"{PROCESSOR_NAME}_trend_{days}d", end_date, ext="json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    # 返回精简结果
    return {
        "period": trend["period"],
        "total_inflow": trend["total_inflow"],
        "avg_inflow": trend["avg_inflow"],
        "trend": trend["trend"],
        "summary": f"近 {days} 天北向资金累计{'流入' if trend['total_inflow'] > 0 else '流出'} {abs(trend['total_inflow'])} 亿元"
    }


# ========== 信号提取方法（用于回测） ==========

def extract_northbound_signals(
    daily_data: list[dict],
    consecutive_threshold: int = 3,
    large_inflow_threshold: float = 50.0,  # 亿元
    large_outflow_threshold: float = 50.0,  # 亿元
) -> list[dict]:
    """提取北向资金流向信号

    Args:
        daily_data: 每日资金数据（按日期升序排列）
        consecutive_threshold: 连续天数阈值（默认 3 天）
        large_inflow_threshold: 大幅流入阈值（亿元，默认 50）
        large_outflow_threshold: 大幅流出阈值（亿元，默认 50）

    Returns:
        信号列表
    """
    if not daily_data or len(daily_data) < 2:
        return []

    # 确保数据按日期升序排列
    daily_data = sorted(daily_data, key=lambda x: x["date"])

    signals = []

    # 追踪连续流入/流出状态
    consecutive_inflow = 0
    consecutive_outflow = 0

    for i in range(len(daily_data)):
        curr = daily_data[i]
        curr_date = curr["date"]
        curr_flow = float(curr["total_flow"])
        curr_status = curr.get("status", "")

        # 更新连续状态
        if curr_flow > 0:
            consecutive_inflow += 1
            consecutive_outflow = 0
        elif curr_flow < 0:
            consecutive_outflow += 1
            consecutive_inflow = 0
        else:
            consecutive_inflow = 0
            consecutive_outflow = 0

        # 买入信号 1：连续流入 + 大幅流入
        if (
            consecutive_inflow >= consecutive_threshold
            and curr_flow >= large_inflow_threshold
        ):
            signals.append({
                "date": curr_date,
                "action": "buy",
                "score": 1,
                "reason": f"连续{consecutive_inflow}日流入+大幅流入({curr_flow:.2f}亿)",
                "metadata": {
                    "total_flow": round(curr_flow, 2),
                    "consecutive_days": consecutive_inflow,
                    "status": curr_status,
                }
            })

        # 卖出信号 1：连续流出 + 大幅流出
        elif (
            consecutive_outflow >= consecutive_threshold
            and curr_flow <= -large_outflow_threshold
        ):
            signals.append({
                "date": curr_date,
                "action": "sell",
                "score": -1,
                "reason": f"连续{consecutive_outflow}日流出+大幅流出({curr_flow:.2f}亿)",
                "metadata": {
                    "total_flow": round(curr_flow, 2),
                    "consecutive_days": consecutive_outflow,
                    "status": curr_status,
                }
            })

        # 趋势转折信号
        elif i > 0:
            prev_flow = float(daily_data[i - 1]["total_flow"])

            # 买入信号 2：流出转流入（趋势转折向上）
            if prev_flow < 0 and curr_flow > 0:
                # 流入力度要足够大
                if abs(curr_flow) > abs(prev_flow) * 1.5 or curr_flow > 10:
                    signals.append({
                        "date": curr_date,
                        "action": "buy",
                        "score": 1,
                        "reason": f"流出转流入({prev_flow:.2f}亿 -> {curr_flow:.2f}亿)",
                        "metadata": {
                            "total_flow": round(curr_flow, 2),
                            "prev_flow": round(prev_flow, 2),
                            "status": curr_status,
                        }
                    })

            # 卖出信号 2：流入转流出（趋势转折向下）
            elif prev_flow > 0 and curr_flow < 0:
                # 流出力度要足够大
                if abs(curr_flow) > abs(prev_flow) * 1.5 or abs(curr_flow) > 10:
                    signals.append({
                        "date": curr_date,
                        "action": "sell",
                        "score": -1,
                        "reason": f"流入转流出({prev_flow:.2f}亿 -> {curr_flow:.2f}亿)",
                        "metadata": {
                            "total_flow": round(curr_flow, 2),
                            "prev_flow": round(prev_flow, 2),
                            "status": curr_status,
                        }
                    })

    return signals


def save_signal_file(
    daily_data: list[dict],
    params: dict,
    signals: list[dict],
) -> Path:
    """保存信号文件

    Args:
        daily_data: 原始数据
        params: 参数
        signals: 信号列表

    Returns:
        信号文件路径
    """
    signal_id = build_signal_id("northbound_flow", params)

    date_range = {}
    if daily_data:
        sorted_data = sorted(daily_data, key=lambda x: x["date"])
        date_range = {
            "start": sorted_data[0]["date"],
            "end": sorted_data[-1]["date"],
        }

    signal_data = build_signal_data(
        signal_type="northbound_flow",
        stock_code=MARKET_CODE,
        signal_id=signal_id,
        signals=signals,
        params=params,
        date_range=date_range,
    )

    return save_signal(signal_data)


async def process_signals(
    days: int,
    end_date: str,
    consecutive_threshold: int = 3,
    large_inflow_threshold: float = 50.0,
    large_outflow_threshold: float = 50.0,
    signal_only: bool = False,
) -> dict:
    """
    处理信号输出

    Args:
        days: 天数
        end_date: 结束日期
        consecutive_threshold: 连续天数阈值
        large_inflow_threshold: 大幅流入阈值（亿元）
        large_outflow_threshold: 大幅流出阈值（亿元）
        signal_only: 只输出信号

    Returns:
        处理结果
    """
    # 获取趋势数据（包含历史数据）
    trend = await fetch_trend(days, end_date)
    daily_data = trend["daily_data"]

    if not daily_data:
        return {"error": "无数据"}

    # 信号参数
    signal_params = {
        "days": days,
        "consecutive_threshold": consecutive_threshold,
        "large_inflow_threshold": large_inflow_threshold,
        "large_outflow_threshold": large_outflow_threshold,
    }

    # 提取信号
    signals = extract_northbound_signals(
        daily_data,
        consecutive_threshold=consecutive_threshold,
        large_inflow_threshold=large_inflow_threshold,
        large_outflow_threshold=large_outflow_threshold,
    )

    # 保存信号文件
    if signals:
        path = save_signal_file(daily_data, signal_params, signals)
    else:
        path = None

    # 如果只输出信号
    if signal_only:
        if signals:
            return {
                "signal_file": str(path),
                "total_signals": len(signals),
                "buy_signals": sum(1 for s in signals if s["action"] == "buy"),
                "sell_signals": sum(1 for s in signals if s["action"] == "sell"),
            }
        else:
            return {"message": "未检测到信号"}

    # 同时保存趋势分析结果
    output_path = get_output_path(SKILL_NAME, f"{PROCESSOR_NAME}_signals_{days}d", end_date, ext="json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = {
        "period": trend["period"],
        "total_inflow": trend["total_inflow"],
        "avg_inflow": trend["avg_inflow"],
        "trend": trend["trend"],
        "signals": signals,
        "signal_params": signal_params,
    }
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    # 返回精简结果
    return {
        "period": trend["period"],
        "total_inflow": trend["total_inflow"],
        "trend": trend["trend"],
        "signals_count": len(signals),
        "signal_file": str(path) if path else None,
        "latest_signals": signals[-3:] if signals else [],  # 最近 3 个信号
    }


async def main():
    """主入口"""
    args = parse_args()

    if args.action == "daily":
        result = await process_daily(args.date, args.top_n)
    elif args.action == "stock":
        result = await process_stock(args.date, args.top_n)
    elif args.action == "trend":
        result = await process_trend(args.days, args.date)
    elif args.action == "signals":
        result = await process_signals(
            days=args.days,
            end_date=args.date,
            consecutive_threshold=args.consecutive,
            large_inflow_threshold=args.large_inflow,
            large_outflow_threshold=args.large_outflow,
            signal_only=args.signal_only,
        )
    else:
        result = {"error": f"未知操作: {args.action}"}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
