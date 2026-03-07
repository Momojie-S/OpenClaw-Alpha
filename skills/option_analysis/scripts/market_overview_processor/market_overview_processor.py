# -*- coding: utf-8 -*-
"""期权市场概况 Processor"""

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_args():
    parser = argparse.ArgumentParser(description="期权市场概况")
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="日期（默认今天）"
    )
    parser.add_argument(
        "--output",
        help="输出文件路径（可选）"
    )
    return parser.parse_args()


async def get_market_overview(date: str) -> dict[str, Any]:
    """获取期权市场概况"""
    from ..option_data_fetcher import fetch

    result = {
        "date": date,
        "sse": {},
        "szse": {},
        "summary": {
            "total_volume": 0,
            "total_oi": 0,
            "avg_pcr": 0
        }
    }

    # 获取上交所数据
    try:
        sse_stats = await fetch("daily_stats_sse", date=date)
        if sse_stats:
            result["sse"] = _process_exchange_stats(sse_stats, "sse")
    except Exception as e:
        result["sse"] = {"error": str(e)}

    # 获取深交所数据
    try:
        szse_stats = await fetch("daily_stats_szse", date=date)
        if szse_stats:
            result["szse"] = _process_exchange_stats(szse_stats, "szse")
    except Exception as e:
        result["szse"] = {"error": str(e)}

    # 计算汇总
    result["summary"] = _calc_summary(result["sse"], result["szse"])

    return result


def _process_exchange_stats(stats: list, exchange: str) -> dict:
    """处理交易所统计数据"""
    etf_options = []
    total_volume = 0
    total_oi = 0
    pcr_values = []

    for stat in stats:
        call_vol = stat.get("认购成交量", 0) or 0
        put_vol = stat.get("认沽成交量", 0) or 0
        call_oi = stat.get("未平仓认购合约数", 0) or 0
        put_oi = stat.get("未平仓认沽合约数", 0) or 0
        pcr = stat.get("认沽/认购", 0) or 0

        name = stat.get("名称", stat.get("期权名称", "未知"))

        etf_options.append({
            "name": name,
            "volume": int(call_vol + put_vol),
            "oi": int(call_oi + put_oi),
            "pcr": round(pcr, 2)
        })

        total_volume += call_vol + put_vol
        total_oi += call_oi + put_oi
        if pcr > 0:
            pcr_values.append(pcr)

    return {
        "etf_options": etf_options,
        "total_volume": int(total_volume),
        "total_oi": int(total_oi),
        "avg_pcr": round(sum(pcr_values) / len(pcr_values), 2) if pcr_values else 0
    }


def _calc_summary(sse_data: dict, szse_data: dict) -> dict:
    """计算市场汇总"""
    total_volume = 0
    total_oi = 0
    pcr_values = []

    for data in [sse_data, szse_data]:
        if data and "total_volume" in data:
            total_volume += data.get("total_volume", 0)
            total_oi += data.get("total_oi", 0)
            if data.get("avg_pcr", 0) > 0:
                pcr_values.append(data["avg_pcr"])

    return {
        "total_volume": int(total_volume),
        "total_oi": int(total_oi),
        "avg_pcr": round(sum(pcr_values) / len(pcr_values), 2) if pcr_values else 0
    }


def get_output_path(date: str) -> Path:
    """获取输出文件路径"""
    return Path(f".openclaw_alpha/option_analysis/{date}/market_overview.json")


def main():
    args = parse_args()

    result = asyncio.run(get_market_overview(args.date))

    # 保存到文件
    output_path = Path(args.output) if args.output else get_output_path(args.date)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    # 打印精简结果
    summary = result["summary"]
    print(json.dumps({
        "date": result["date"],
        "total_volume": summary["total_volume"],
        "total_oi": summary["total_oi"],
        "avg_pcr": summary["avg_pcr"],
        "sse_options": len(result["sse"].get("etf_options", [])),
        "szse_options": len(result["szse"].get("etf_options", []))
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
