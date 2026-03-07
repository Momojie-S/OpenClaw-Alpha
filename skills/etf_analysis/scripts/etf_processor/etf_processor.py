# -*- coding: utf-8 -*-
"""ETF Processor - ETF 行情查询和分析"""

import argparse
import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional

import akshare as ak
import pandas as pd

SKILL_NAME = "etf_analysis"
PROCESSOR_NAME = "etf_processor"


@dataclass
class EtfSpot:
    """ETF 实时行情"""

    code: str
    name: str
    price: float
    change_pct: float
    change: float
    amount: float  # 亿
    volume: float
    open: float
    high: float
    low: float
    prev_close: float


@dataclass
class EtfHistory:
    """ETF 历史数据"""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float


def fetch_spot() -> list[EtfSpot]:
    """
    获取全部 ETF 实时行情

    Returns:
        ETF 行情列表
    """
    try:
        df = ak.fund_etf_category_sina(symbol="ETF基金")
    except Exception:
        return []

    result = []
    for _, row in df.iterrows():
        try:
            # 成交额转换为亿
            amount = float(row["成交额"]) / 1e8 if pd.notna(row["成交额"]) else 0
            # 涨跌幅去掉 % 符号
            change_pct = float(str(row["涨跌幅"]).replace("%", "")) if pd.notna(row["涨跌幅"]) else 0

            etf = EtfSpot(
                code=str(row["代码"]),
                name=str(row["名称"]),
                price=float(row["最新价"]) if pd.notna(row["最新价"]) else 0,
                change_pct=change_pct,
                change=float(row["涨跌额"]) if pd.notna(row["涨跌额"]) else 0,
                amount=round(amount, 2),
                volume=float(row["成交量"]) if pd.notna(row["成交量"]) else 0,
                open=float(row["今开"]) if pd.notna(row["今开"]) else 0,
                high=float(row["最高"]) if pd.notna(row["最高"]) else 0,
                low=float(row["最低"]) if pd.notna(row["最低"]) else 0,
                prev_close=float(row["昨收"]) if pd.notna(row["昨收"]) else 0,
            )
            result.append(etf)
        except (ValueError, KeyError):
            continue

    return result


def fetch_history(symbol: str, days: int = 30) -> list[EtfHistory]:
    """
    获取 ETF 历史数据

    Args:
        symbol: ETF 代码（如 sz159915）
        days: 历史天数

    Returns:
        历史数据列表
    """
    try:
        df = ak.fund_etf_hist_sina(symbol=symbol)
    except Exception:
        return []

    # 按日期倒序，取最近 days 天
    df = df.sort_values("date", ascending=False).head(days)

    result = []
    for _, row in df.iterrows():
        try:
            hist = EtfHistory(
                date=str(row["date"]),
                open=float(row["open"]) if pd.notna(row["open"]) else 0,
                high=float(row["high"]) if pd.notna(row["high"]) else 0,
                low=float(row["low"]) if pd.notna(row["low"]) else 0,
                close=float(row["close"]) if pd.notna(row["close"]) else 0,
                volume=float(row["volume"]) if pd.notna(row["volume"]) else 0,
                amount=float(row["amount"]) / 1e8 if pd.notna(row["amount"]) else 0,
            )
            result.append(hist)
        except (ValueError, KeyError):
            continue

    return result


def filter_spot(
    etfs: list[EtfSpot],
    change_min: Optional[float] = None,
    change_max: Optional[float] = None,
    amount_min: Optional[float] = None,
    keyword: Optional[str] = None,
) -> list[EtfSpot]:
    """
    筛选 ETF 行情

    Args:
        etfs: ETF 列表
        change_min: 涨跌幅下限
        change_max: 涨跌幅上限
        amount_min: 成交额下限（亿）
        keyword: 名称关键词

    Returns:
        筛选后的列表
    """
    result = etfs

    if change_min is not None:
        result = [e for e in result if e.change_pct >= change_min]

    if change_max is not None:
        result = [e for e in result if e.change_pct <= change_max]

    if amount_min is not None:
        result = [e for e in result if e.amount >= amount_min]

    if keyword:
        keyword_lower = keyword.lower()
        result = [e for e in result if keyword_lower in e.name.lower()]

    return result


def sort_spot(etfs: list[EtfSpot], sort_by: str = "change") -> list[EtfSpot]:
    """
    排序 ETF 行情

    Args:
        etfs: ETF 列表
        sort_by: 排序字段 (change/amount/price)

    Returns:
        排序后的列表
    """
    sort_key_map = {
        "change": lambda e: e.change_pct,
        "amount": lambda e: e.amount,
        "price": lambda e: e.price,
    }

    key = sort_key_map.get(sort_by, lambda e: e.change_pct)
    return sorted(etfs, key=key, reverse=True)


def process(
    action: str = "spot",
    symbol: Optional[str] = None,
    change_min: Optional[float] = None,
    change_max: Optional[float] = None,
    amount_min: Optional[float] = None,
    keyword: Optional[str] = None,
    sort_by: str = "change",
    top_n: int = 20,
    days: int = 30,
) -> dict:
    """
    ETF 分析处理

    Args:
        action: 操作类型 (spot/history)
        symbol: ETF 代码（history 必填）
        change_min: 涨跌幅下限
        change_max: 涨跌幅上限
        amount_min: 成交额下限（亿）
        keyword: 名称关键词
        sort_by: 排序字段
        top_n: 返回数量
        days: 历史天数

    Returns:
        处理结果
    """
    if action == "history":
        if not symbol:
            return {"error": "history 模式需要指定 --symbol"}

        history = fetch_history(symbol, days)
        return {
            "code": symbol,
            "data": [asdict(h) for h in history],
            "count": len(history),
        }

    # 获取实时行情
    etfs = fetch_spot()

    # 筛选
    etfs = filter_spot(etfs, change_min, change_max, amount_min, keyword)

    # 排序
    etfs = sort_spot(etfs, sort_by)

    # 取 Top N
    etfs = etfs[:top_n]

    return {
        "data": [asdict(e) for e in etfs],
        "count": len(etfs),
        "filters": {
            "change_min": change_min,
            "change_max": change_max,
            "amount_min": amount_min,
            "keyword": keyword,
        },
    }


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="ETF 行情查询和分析")
    parser.add_argument(
        "--action",
        choices=["spot", "history"],
        default="spot",
        help="操作类型: spot(实时行情) / history(历史数据)",
    )
    parser.add_argument("--symbol", help="ETF 代码（history 必填）")
    parser.add_argument("--change-min", type=float, help="涨跌幅下限 (%%)")
    parser.add_argument("--change-max", type=float, help="涨跌幅上限 (%%)")
    parser.add_argument("--amount-min", type=float, help="成交额下限（亿）")
    parser.add_argument("--keyword", help="名称关键词")
    parser.add_argument(
        "--sort-by",
        choices=["change", "amount", "price"],
        default="change",
        help="排序字段",
    )
    parser.add_argument("--top-n", type=int, default=20, help="返回数量")
    parser.add_argument("--days", type=int, default=30, help="历史天数")

    args = parser.parse_args()

    result = process(
        action=args.action,
        symbol=args.symbol,
        change_min=args.change_min,
        change_max=args.change_max,
        amount_min=args.amount_min,
        keyword=args.keyword,
        sort_by=args.sort_by,
        top_n=args.top_n,
        days=args.days,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
