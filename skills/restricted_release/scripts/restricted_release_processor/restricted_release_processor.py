# -*- coding: utf-8 -*-
"""限售解禁风险监控 Processor"""

import argparse
import asyncio
import json
from datetime import datetime, timedelta

from openclaw_alpha.core.processor_utils import get_output_path

from ..restricted_release_fetcher import fetch


def parse_args():
    parser = argparse.ArgumentParser(description="限售解禁风险监控")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # upcoming: 即将解禁股票
    upcoming_parser = subparsers.add_parser("upcoming", help="查询即将解禁的股票")
    upcoming_parser.add_argument(
        "--days", type=int, default=7, help="查询未来几天（默认7天）"
    )
    upcoming_parser.add_argument(
        "--sort-by",
        choices=["value", "ratio"],
        default="value",
        help="排序方式: value=解禁市值, ratio=占流通市值比例",
    )
    upcoming_parser.add_argument("--top-n", type=int, default=20, help="返回Top N")

    # queue: 单只股票解禁排期
    queue_parser = subparsers.add_parser("queue", help="查询单只股票的解禁排期")
    queue_parser.add_argument("symbol", help="股票代码")
    queue_parser.add_argument("--top-n", type=int, default=10, help="返回Top N")

    # high-risk: 高解禁风险股票
    risk_parser = subparsers.add_parser("high-risk", help="筛选高解禁风险股票")
    risk_parser.add_argument(
        "--days", type=int, default=7, help="查询未来几天（默认7天）"
    )
    risk_parser.add_argument(
        "--min-ratio",
        type=float,
        default=0.1,
        help="最小占流通市值比例（默认0.1即10%）",
    )

    return parser.parse_args()


async def get_upcoming_stocks(days: int, sort_by: str, top_n: int) -> dict:
    """
    获取即将解禁的股票

    Args:
        days: 查询未来几天
        sort_by: 排序方式
        top_n: 返回数量

    Returns:
        包含完整数据和精简结果的字典
    """
    today = datetime.now().strftime("%Y%m%d")
    end_date = (datetime.now() + timedelta(days=days)).strftime("%Y%m%d")

    result = await fetch(
        mode="upcoming", start_date=today, end_date=end_date
    )

    data = result.get("data", [])

    if not data:
        return {"all": [], "top": [], "meta": {"message": "查询时间内无解禁股票"}}

    # 排序
    if sort_by == "value":
        data.sort(key=lambda x: x.get("actual_release_value", 0), reverse=True)
    else:
        data.sort(key=lambda x: x.get("ratio_to_circulation", 0), reverse=True)

    # 保存完整数据
    all_data = data

    # 精简结果
    top_data = data[:top_n]

    return {
        "all": all_data,
        "top": top_data,
        "meta": {
            "start_date": today,
            "end_date": end_date,
            "total_count": len(data),
            "sort_by": sort_by,
        },
    }


async def get_stock_queue(symbol: str, top_n: int) -> dict:
    """
    获取单只股票的解禁排期

    Args:
        symbol: 股票代码
        top_n: 返回数量

    Returns:
        包含完整数据和精简结果的字典
    """
    result = await fetch(mode="queue", symbol=symbol)

    data = result.get("data", [])

    if not data:
        return {"all": [], "top": [], "meta": {"message": f"{symbol} 无解禁记录"}}

    # 按日期降序（最近的在前）
    data.sort(key=lambda x: x.get("release_date", ""), reverse=True)

    all_data = data
    top_data = data[:top_n]

    return {
        "all": all_data,
        "top": top_data,
        "meta": {"symbol": symbol, "total_count": len(data)},
    }


async def get_high_risk_stocks(days: int, min_ratio: float) -> dict:
    """
    筛选高解禁风险股票

    Args:
        days: 查询未来几天
        min_ratio: 最小占流通市值比例

    Returns:
        高风险股票列表
    """
    today = datetime.now().strftime("%Y%m%d")
    end_date = (datetime.now() + timedelta(days=days)).strftime("%Y%m%d")

    result = await fetch(
        mode="upcoming", start_date=today, end_date=end_date
    )

    data = result.get("data", [])

    # 筛选高风险股票
    high_risk = [
        item
        for item in data
        if item.get("ratio_to_circulation", 0) >= min_ratio
    ]

    # 按比例降序
    high_risk.sort(key=lambda x: x.get("ratio_to_circulation", 0), reverse=True)

    return {
        "data": high_risk,
        "meta": {
            "start_date": today,
            "end_date": end_date,
            "min_ratio": min_ratio,
            "total_count": len(data),
            "high_risk_count": len(high_risk),
        },
    }


def format_upcoming(data: list[dict]) -> str:
    """格式化即将解禁股票列表"""
    lines = [f"即将解禁股票 (共 {len(data)} 只):\n"]
    lines.append(
        f"{'代码':<8} {'名称':<8} {'解禁日期':<12} {'解禁市值(亿)':<12} {'占流通市值':<12}"
    )
    lines.append("-" * 60)

    for item in data:
        code = item.get("code", "")
        name = item.get("name", "")
        date = item.get("release_date", "")
        value = item.get("actual_release_value", 0) / 1e8
        ratio = item.get("ratio_to_circulation", 0) * 100

        lines.append(
            f"{code:<8} {name:<8} {date:<12} {value:<12.2f} {ratio:<11.2f}%"
        )

    return "\n".join(lines)


def format_queue(data: list[dict]) -> str:
    """格式化解禁排期"""
    lines = [f"解禁排期 (共 {len(data)} 次):\n"]
    lines.append(
        f"{'解禁日期':<12} {'股东数':<8} {'解禁市值(亿)':<12} {'占流通市值':<10} {'类型':<15}"
    )
    lines.append("-" * 70)

    for item in data:
        date = item.get("release_date", "")
        shareholders = item.get("shareholder_count", 0)
        value = item.get("actual_release_value", 0) / 1e8
        ratio = item.get("ratio_to_circulation", 0) * 100
        rtype = item.get("restricted_type", "")[:15]

        lines.append(
            f"{date:<12} {shareholders:<8} {value:<12.2f} {ratio:<10.2f}% {rtype:<15}"
        )

    return "\n".join(lines)


def format_high_risk(data: list[dict], min_ratio: float) -> str:
    """格式化高风险股票列表"""
    if not data:
        return f"无高风险股票（占流通市值 >= {min_ratio*100:.1f}%）"

    lines = [f"高风险解禁股票 (占流通市值 >= {min_ratio*100:.1f}%, 共 {len(data)} 只):\n"]
    lines.append(
        f"{'代码':<8} {'名称':<8} {'解禁日期':<12} {'解禁市值(亿)':<12} {'占流通市值':<12} {'风险等级':<8}"
    )
    lines.append("-" * 72)

    for item in data:
        code = item.get("code", "")
        name = item.get("name", "")
        date = item.get("release_date", "")
        value = item.get("actual_release_value", 0) / 1e8
        ratio = item.get("ratio_to_circulation", 0) * 100

        # 风险等级
        if ratio >= 50:
            risk = "极高"
        elif ratio >= 30:
            risk = "高"
        elif ratio >= 20:
            risk = "中"
        else:
            risk = "低"

        lines.append(
            f"{code:<8} {name:<8} {date:<12} {value:<12.2f} {ratio:<11.2f}% {risk:<8}"
        )

    return "\n".join(lines)


async def main():
    args = parse_args()

    if args.command == "upcoming":
        result = await get_upcoming_stocks(args.days, args.sort_by, args.top_n)

        # 保存完整数据
        output_path = get_output_path(
            "restricted_release", "upcoming", ext="json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result["all"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # 打印精简结果
        print(format_upcoming(result["top"]))
        print(f"\n完整数据已保存至: {output_path}")

    elif args.command == "queue":
        result = await get_stock_queue(args.symbol, args.top_n)

        # 保存完整数据
        output_path = get_output_path(
            "restricted_release", f"queue_{args.symbol}", ext="json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result["all"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # 打印精简结果
        print(format_queue(result["top"]))
        print(f"\n完整数据已保存至: {output_path}")

    elif args.command == "high-risk":
        result = await get_high_risk_stocks(args.days, args.min_ratio)

        # 保存数据
        output_path = get_output_path(
            "restricted_release", "high_risk", ext="json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result["data"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # 打印结果
        print(format_high_risk(result["data"], args.min_ratio))
        print(f"\n完整数据已保存至: {output_path}")

    else:
        print("请指定子命令: upcoming, queue, high-risk")
        print("使用 --help 查看帮助")


if __name__ == "__main__":
    asyncio.run(main())
