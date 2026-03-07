# -*- coding: utf-8 -*-
"""北向资金分析 Processor"""

import argparse
import asyncio
import json
from datetime import datetime

from openclaw_alpha.core.processor_utils import get_output_path
from skills.northbound_flow.scripts.flow_fetcher import fetch_daily, fetch_stocks, fetch_trend


# 常量定义
SKILL_NAME = "northbound_flow"
PROCESSOR_NAME = "northbound"


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="北向资金分析")
    parser.add_argument(
        "--action",
        choices=["daily", "stock", "trend"],
        default="daily",
        help="查询类型：daily（每日净流入）、stock（个股流向）、trend（资金趋势）"
    )
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="查询日期（默认今天）"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=5,
        help="趋势天数（默认 5 天）"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Top N（默认 10）"
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


async def main():
    """主入口"""
    args = parse_args()

    if args.action == "daily":
        result = await process_daily(args.date, args.top_n)
    elif args.action == "stock":
        result = await process_stock(args.date, args.top_n)
    elif args.action == "trend":
        result = await process_trend(args.days, args.date)
    else:
        result = {"error": f"未知操作: {args.action}"}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
