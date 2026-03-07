# -*- coding: utf-8 -*-
"""市场融资融券汇总 Processor"""

import argparse
import json
from datetime import datetime
from typing import Any

import akshare as ak
import pandas as pd


SKILL_NAME = "margin_trading"
PROCESSOR_NAME = "market_margin"


def get_sh_margin() -> pd.DataFrame:
    """获取沪市融资融券数据"""
    return ak.macro_china_market_margin_sh()


def get_sz_margin() -> pd.DataFrame:
    """获取深市融资融券数据"""
    return ak.macro_china_market_margin_sz()


def calculate_change_pct(df: pd.DataFrame, date: str) -> float:
    """计算融资余额环比变化

    Args:
        df: 原始数据
        date: 当前日期 (YYYY-MM-DD)

    Returns:
        环比变化百分比
    """
    # 找到当前日期的数据
    current_idx = df[df["日期"] == date].index
    if len(current_idx) == 0:
        return 0.0

    current_idx = current_idx[0]
    if current_idx == 0:
        return 0.0

    current_balance = df.loc[current_idx, "融资余额"]
    prev_balance = df.loc[current_idx - 1, "融资余额"]

    if prev_balance == 0:
        return 0.0

    return round((current_balance - prev_balance) / prev_balance * 100, 2)


def get_latest_trading_day(df: pd.DataFrame) -> str:
    """获取最新交易日"""
    return df.iloc[-1]["日期"]


def process(date: str | None = None, output: str = "text") -> dict[str, Any]:
    """处理市场融资融券数据

    Args:
        date: 查询日期，默认最新
        output: 输出格式 (text/json)

    Returns:
        处理后的数据
    """
    # 获取原始数据
    sh_df = get_sh_margin()
    sz_df = get_sz_margin()

    # 确定日期
    if date is None:
        date = get_latest_trading_day(sh_df)

    # 计算环比
    sh_change = calculate_change_pct(sh_df, date)
    sz_change = calculate_change_pct(sz_df, date)

    # 获取当日数据
    sh_row = sh_df[sh_df["日期"] == date].iloc[0]
    sz_row = sz_df[sz_df["日期"] == date].iloc[0]

    # 转换为亿元
    sh_balance = round(sh_row["融资余额"] / 1e8, 2)
    sh_buy = round(sh_row["融资买入额"] / 1e8, 2)
    sz_balance = round(sz_row["融资余额"] / 1e8, 2)
    sz_buy = round(sz_row["融资买入额"] / 1e8, 2)

    total_balance = round(sh_balance + sz_balance, 2)

    # 判断杠杆水平
    avg_change = (sh_change + sz_change) / 2
    if avg_change > 2:
        leverage_level = "高"
    elif avg_change < -2:
        leverage_level = "低"
    else:
        leverage_level = "正常"

    result = {
        "date": date,
        "sh_market": {
            "financing_balance": sh_balance,
            "financing_buy": sh_buy,
            "change_pct": sh_change,
        },
        "sz_market": {
            "financing_balance": sz_balance,
            "financing_buy": sz_buy,
            "change_pct": sz_change,
        },
        "total": {
            "financing_balance": total_balance,
            "avg_change_pct": round(avg_change, 2),
        },
        "leverage_level": leverage_level,
    }

    if output == "text":
        print(format_text(result))

    return result


def format_text(data: dict) -> str:
    """格式化为文本"""
    lines = [
        f"# 市场融资融券汇总 - {data['date']}",
        "",
        "## 杠杆水平",
        f"**{data['leverage_level']}** (平均环比: {data['total']['avg_change_pct']}%)",
        "",
        "## 沪市",
        f"- 融资余额: {data['sh_market']['financing_balance']} 亿",
        f"- 融资买入: {data['sh_market']['financing_buy']} 亿",
        f"- 环比变化: {data['sh_market']['change_pct']}%",
        "",
        "## 深市",
        f"- 融资余额: {data['sz_market']['financing_balance']} 亿",
        f"- 融资买入: {data['sz_market']['financing_buy']} 亿",
        f"- 环比变化: {data['sz_market']['change_pct']}%",
        "",
        "## 汇总",
        f"- 两市融资余额: {data['total']['financing_balance']} 亿",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="市场融资融券汇总")
    parser.add_argument("--date", default=None, help="查询日期 (YYYY-MM-DD)")
    parser.add_argument("--output", default="text", choices=["text", "json"])
    args = parser.parse_args()

    result = process(date=args.date, output=args.output)

    if args.output == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
