# -*- coding: utf-8 -*-
"""个股融资融券明细 Processor"""

import argparse
import json
from datetime import datetime
from typing import Any

import akshare as ak
import pandas as pd


SKILL_NAME = "margin_trading"
PROCESSOR_NAME = "stock_margin"


def get_sh_stocks(date: str) -> pd.DataFrame:
    """获取沪市个股融资融券数据

    Args:
        date: 日期 (YYYYMMDD)

    Returns:
        个股数据
    """
    try:
        df = ak.stock_margin_detail_sse(date=date)
        return df
    except Exception:
        return pd.DataFrame()


def get_sz_stocks(date: str) -> pd.DataFrame:
    """获取深市个股融资融券数据

    Args:
        date: 日期 (YYYYMMDD)

    Returns:
        个股数据
    """
    try:
        df = ak.stock_margin_detail_szse(date=date)
        return df
    except Exception:
        return pd.DataFrame()


def normalize_df(df: pd.DataFrame, column_mapping: dict) -> pd.DataFrame:
    """标准化数据框列名

    Args:
        df: 原始数据
        column_mapping: 列名映射

    Returns:
        标准化后的数据
    """
    if df.empty:
        return pd.DataFrame()

    # 重命名列名
    df = df.rename(columns=column_mapping)

    # 只保留需要的列
    columns = ["code", "name", "financing_balance", "financing_buy", "securities_balance", "securities_sell"]
    available_columns = [c for c in columns if c in df.columns]

    if not available_columns:
        return pd.DataFrame()

    return df[available_columns]


def merge_stocks(sh_df: pd.DataFrame, sz_df: pd.DataFrame) -> pd.DataFrame:
    """合并沪深数据

    Args:
        sh_df: 沪市数据
        sz_df: 深市数据

    Returns:
        合并后的数据
    """
    # 沪市列名映射
    sh_mapping = {
        "标的证券代码": "code",
        "标的证券简称": "name",
        "融资余额": "financing_balance",
        "融资买入额": "financing_buy",
        "融券余量": "securities_balance",
        "融券卖出量": "securities_sell",
    }

    # 深市列名映射
    sz_mapping = {
        "证券代码": "code",
        "证券简称": "name",
        "融资余额": "financing_balance",
        "融资买入额": "financing_buy",
        "融券余量": "securities_balance",
        "融券卖出量": "securities_sell",
    }

    # 标准化数据
    sh_normalized = normalize_df(sh_df, sh_mapping)
    sz_normalized = normalize_df(sz_df, sz_mapping)

    if sh_normalized.empty and sz_normalized.empty:
        return pd.DataFrame()

    if sh_normalized.empty:
        return sz_normalized

    if sz_normalized.empty:
        return sh_normalized

    return pd.concat([sh_normalized, sz_normalized], ignore_index=True)


def process(
    margin_type: str = "financing",
    top_n: int = 20,
    date: str | None = None,
    output: str = "text",
) -> dict[str, Any]:
    """处理个股融资融券数据

    Args:
        margin_type: 类型 (financing/securities)
        top_n: 返回数量
        date: 查询日期 (YYYY-MM-DD)
        output: 输出格式

    Returns:
        处理后的数据
    """
    # 转换日期格式
    if date is None:
        # 获取最近的交易日（简单处理：使用前一个工作日）
        today = datetime.now()
        # 往前找最近的交易日（跳过周末）
        while today.weekday() >= 5:  # 5=周六, 6=周日
            today = today.replace(day=today.day - 1)
        date_str = today.strftime("%Y%m%d")
        date = today.strftime("%Y-%m-%d")
    else:
        date_str = date.replace("-", "")

    # 获取数据
    sh_df = get_sh_stocks(date_str)
    sz_df = get_sz_stocks(date_str)

    # 合并
    merged_df = merge_stocks(sh_df, sz_df)

    if merged_df.empty:
        result = {
            "date": date,
            "type": margin_type,
            "stocks": [],
            "message": "无数据",
        }
        if output == "text":
            print("无数据")
        return result

    # 排序
    if margin_type == "financing":
        sort_col = "financing_balance"
    else:
        sort_col = "securities_balance"

    if sort_col in merged_df.columns:
        merged_df = merged_df.sort_values(by=sort_col, ascending=False)

    # 取 Top N
    top_df = merged_df.head(top_n)

    # 转换为列表
    stocks = []
    for _, row in top_df.iterrows():
        stock = {
            "code": str(row.get("code", "")),
            "name": str(row.get("name", "")),
        }
        if "financing_balance" in row:
            stock["financing_balance"] = round(float(row["financing_balance"]) / 1e8, 2)
        if "financing_buy" in row:
            stock["financing_buy"] = round(float(row["financing_buy"]) / 1e8, 2)
        if "securities_balance" in row:
            stock["securities_balance"] = int(row["securities_balance"])
        if "securities_sell" in row:
            stock["securities_sell"] = int(row["securities_sell"])
        stocks.append(stock)

    result = {
        "date": date,
        "type": margin_type,
        "stocks": stocks,
    }

    if output == "text":
        print(format_text(result))

    return result


def format_text(data: dict) -> str:
    """格式化为文本"""
    margin_type = "融资" if data["type"] == "financing" else "融券"

    lines = [
        f"# 个股{margin_type}余额 Top {len(data['stocks'])} - {data['date']}",
        "",
    ]

    if not data["stocks"]:
        lines.append("无数据")
        return "\n".join(lines)

    # 表头
    if data["type"] == "financing":
        lines.append("| 排名 | 代码 | 名称 | 融资余额(亿) | 融资买入(亿) |")
        lines.append("|------|------|------|-------------|-------------|")
        for i, stock in enumerate(data["stocks"], 1):
            lines.append(
                f"| {i} | {stock['code']} | {stock['name']} | "
                f"{stock.get('financing_balance', 0)} | {stock.get('financing_buy', 0)} |"
            )
    else:
        lines.append("| 排名 | 代码 | 名称 | 融券余量(股) | 融券卖出(股) |")
        lines.append("|------|------|------|------------|------------|")
        for i, stock in enumerate(data["stocks"], 1):
            lines.append(
                f"| {i} | {stock['code']} | {stock['name']} | "
                f"{stock.get('securities_balance', 0):,} | {stock.get('securities_sell', 0):,} |"
            )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="个股融资融券明细")
    parser.add_argument(
        "--type",
        default="financing",
        choices=["financing", "securities"],
        help="类型: financing(融资) / securities(融券)",
    )
    parser.add_argument("--top-n", type=int, default=20, help="返回数量")
    parser.add_argument("--date", default=None, help="查询日期 (YYYY-MM-DD)")
    parser.add_argument("--output", default="text", choices=["text", "json"])
    args = parser.parse_args()

    result = process(
        margin_type=args.type,
        top_n=args.top_n,
        date=args.date,
        output=args.output,
    )

    if args.output == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
