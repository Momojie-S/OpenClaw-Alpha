# -*- coding: utf-8 -*-
"""龙虎榜分析 Processor"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from openclaw_alpha.core.processor_utils import get_output_path
from openclaw_alpha.skills.lhb_tracker.lhb_fetcher import fetch_daily, fetch_stock_history


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="龙虎榜追踪")
    parser.add_argument("--action", choices=["daily", "stock"], default="daily", help="操作类型")
    parser.add_argument("--date", default=None, help="日期 YYYY-MM-DD（默认最近交易日）")
    parser.add_argument("--symbol", default=None, help="股票代码（stock 模式必需）")
    parser.add_argument("--days", type=int, default=5, help="历史天数（stock 模式）")
    parser.add_argument("--top-n", type=int, default=10, help="返回数量")
    return parser.parse_args()


async def process_daily(date: str | None, top_n: int) -> dict:
    """
    处理每日龙虎榜

    Args:
        date: 日期
        top_n: 返回数量

    Returns:
        处理结果
    """
    # 获取数据
    data = await fetch_daily(date)

    if not data:
        return {
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "total_count": 0,
            "message": "无龙虎榜数据",
            "top_inflow": [],
            "top_outflow": [],
        }

    # 获取日期
    actual_date = data[0]["date"] if data else (date or datetime.now().strftime("%Y-%m-%d"))

    # 按净买入排序
    sorted_data = sorted(data, key=lambda x: x["net_buy"], reverse=True)

    # Top N 净买入
    top_inflow = []
    for stock in sorted_data[:top_n]:
        # 分析买卖方类型
        buy_type = analyze_buyer_type(stock)
        top_inflow.append({
            "code": stock["code"],
            "name": stock["name"],
            "net_buy": round(stock["net_buy"] / 1e8, 2),  # 转换为亿
            "change_pct": round(stock["change_pct"], 2),
            "reason": stock["reason"],
            "buy_type": buy_type,
        })

    # Top N 净卖出
    top_outflow = []
    for stock in reversed(sorted_data[-top_n:]):
        if stock["net_buy"] < 0:  # 只显示净卖出的
            top_outflow.append({
                "code": stock["code"],
                "name": stock["name"],
                "net_buy": round(stock["net_buy"] / 1e8, 2),  # 转换为亿
                "change_pct": round(stock["change_pct"], 2),
                "reason": stock["reason"],
            })

    # 统计
    total_buy = sum(s["buy_amount"] for s in data)
    total_sell = sum(s["sell_amount"] for s in data)
    total_net = total_buy - total_sell

    result = {
        "date": actual_date,
        "total_count": len(data),
        "total_buy": round(total_buy / 1e8, 2),
        "total_sell": round(total_sell / 1e8, 2),
        "total_net": round(total_net / 1e8, 2),
        "top_inflow": top_inflow,
        "top_outflow": top_outflow,
    }

    # 保存完整数据
    output_path = get_output_path("lhb_tracker", "lhb_daily", actual_date, ext="json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return result


async def process_stock(symbol: str, days: int, end_date: str | None, top_n: int) -> dict:
    """
    处理个股龙虎榜

    Args:
        symbol: 股票代码
        days: 历史天数
        end_date: 结束日期
        top_n: 返回数量

    Returns:
        处理结果
    """
    # 计算日期范围
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=days * 2)  # 多查一些，因为可能不是每个交易日都上榜

    start_date = start_dt.strftime("%Y-%m-%d")
    actual_end_date = end_dt.strftime("%Y-%m-%d")

    # 获取数据
    data = await fetch_stock_history(symbol, start_date, actual_end_date)

    if not data:
        return {
            "symbol": symbol,
            "period": f"{start_date} ~ {actual_end_date}",
            "message": "无龙虎榜记录",
            "summary": None,
            "details": [],
        }

    # 按日期排序（最新在前）
    data.sort(key=lambda x: x["date"], reverse=True)

    # 只取最近 N 个记录
    recent_data = data[:days]

    # 统计
    total_net_buy = sum(d["net_buy"] for d in recent_data)
    org_buy = 0
    retail_buy = 0
    north_buy = 0

    for d in recent_data:
        for buyer in d["buyers"]:
            if buyer["type"] == "机构":
                org_buy += buyer["amount"]
            elif buyer["type"] == "北向":
                north_buy += buyer["amount"]
            else:
                retail_buy += buyer["amount"]

    # 分析买卖方类型
    buy_types = set()
    for d in recent_data:
        for buyer in d["buyers"]:
            buy_types.add(buyer["type"])

    result = {
        "symbol": symbol,
        "name": data[0].get("name", "") if data else "",
        "period": f"{recent_data[-1]['date'] if recent_data else start_date} ~ {recent_data[0]['date'] if recent_data else actual_end_date}",
        "summary": {
            "appearances": len(recent_data),
            "total_net_buy": round(total_net_buy / 1e8, 2),
            "org_buy": round(org_buy / 1e8, 2),
            "retail_buy": round(retail_buy / 1e8, 2),
            "north_buy": round(north_buy / 1e8, 2),
            "main_buyer": max(buy_types, key=lambda t: {"机构": 3, "北向": 2, "游资": 1}.get(t, 0)) if buy_types else "",
        },
        "details": recent_data[:top_n],
    }

    # 保存完整数据
    output_path = get_output_path("lhb_tracker", f"lhb_stock_{symbol}", actual_end_date, ext="json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return result


def analyze_buyer_type(stock: dict) -> str:
    """
    分析买卖方类型

    Args:
        stock: 股票数据

    Returns:
        类型描述
    """
    # 由于 daily 接口没有详细的买卖方信息，这里根据净买入金额粗略判断
    # 如果净买入金额较大（>1亿），可能是机构参与
    net_buy = stock.get("net_buy", 0)
    if net_buy > 1e8:
        return "机构+游资"
    elif net_buy > 0:
        return "游资"
    else:
        return "卖盘为主"


def main():
    args = parse_args()

    if args.action == "daily":
        result = asyncio.run(process_daily(args.date, args.top_n))
    elif args.action == "stock":
        if not args.symbol:
            print("错误：stock 模式需要指定 --symbol")
            return
        result = asyncio.run(process_stock(args.symbol, args.days, args.date, args.top_n))

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
