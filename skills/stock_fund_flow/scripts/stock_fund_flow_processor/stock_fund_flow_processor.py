# -*- coding: utf-8 -*-
"""个股资金流向分析 Processor"""

import argparse
import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import akshare as ak
import pandas as pd

from openclaw_alpha.core.processor_utils import get_output_path

SKILL_NAME = "stock_fund_flow"
PROCESSOR_NAME = "stock_fund_flow"


@dataclass
class FundFlowSummary:
    """资金流向汇总"""

    period: str  # 周期：今日/近5日/近10日/近20日
    main_net_inflow: float  # 主力净流入（元）
    main_net_ratio: float  # 主力净占比（%）
    super_large_net_inflow: float  # 超大单净流入
    large_net_inflow: float  # 大单净流入
    medium_net_inflow: float  # 中单净流入
    small_net_inflow: float  # 小单净流入


@dataclass
class FundFlowTrend:
    """资金流向趋势"""

    trend: str  # 持续流入/持续流出/震荡
    description: str  # 趋势描述
    consecutive_days: int  # 连续流入/流出天数
    avg_daily_inflow: float  # 日均净流入


@dataclass
class PriceCorrelation:
    """资金与价格关联"""

    correlation: str  # 资金推动/资金背离/无明显关联
    description: str  # 关联描述


@dataclass
class FundFlowResult:
    """资金流向分析结果"""

    code: str
    name: str
    latest_date: str
    latest_price: float
    latest_change: float
    summaries: list[FundFlowSummary]
    trend: FundFlowTrend
    price_correlation: PriceCorrelation


def normalize_stock_code(code: str) -> tuple[str, str]:
    """
    规范化股票代码，返回 (纯代码, 市场)

    Args:
        code: 股票代码或名称

    Returns:
        (纯代码, 市场) 如 ("000001", "sz")
    """
    # 去除后缀
    code = code.upper().replace(".SZ", "").replace(".SH", "")

    # 判断市场
    if code.startswith("6"):
        return code, "sh"
    else:
        return code, "sz"


def fetch_fund_flow(code: str) -> pd.DataFrame:
    """
    获取个股资金流向数据

    Args:
        code: 股票代码

    Returns:
        资金流向 DataFrame
    """
    pure_code, market = normalize_stock_code(code)
    df = ak.stock_individual_fund_flow(stock=pure_code, market=market)

    # 规范化列名
    column_mapping = {
        "日期": "date",
        "收盘价": "close",
        "涨跌幅": "pct_change",
        "主力净流入-净额": "main_net_inflow",
        "主力净流入-净占比": "main_net_ratio",
        "超大单净流入-净额": "super_large_net_inflow",
        "超大单净流入-净占比": "super_large_net_ratio",
        "大单净流入-净额": "large_net_inflow",
        "大单净流入-净占比": "large_net_ratio",
        "中单净流入-净额": "medium_net_inflow",
        "中单净流入-净占比": "medium_net_ratio",
        "小单净流入-净额": "small_net_inflow",
        "小单净流入-净占比": "small_net_ratio",
    }
    df = df.rename(columns=column_mapping)

    # 按日期降序（最新在前）
    df = df.sort_values("date", ascending=False).reset_index(drop=True)

    return df


def calculate_summaries(df: pd.DataFrame, periods: list[int]) -> list[FundFlowSummary]:
    """
    计算各周期资金流向汇总

    Args:
        df: 资金流向数据
        periods: 周期列表 [1, 5, 10, 20]

    Returns:
        各周期汇总列表
    """
    summaries = []
    period_names = {1: "今日", 5: "近5日", 10: "近10日", 20: "近20日"}

    for period in periods:
        if len(df) < period:
            continue

        subset = df.head(period)

        # 计算汇总（取最新一天的占比，净额求和）
        summary = FundFlowSummary(
            period=period_names.get(period, f"近{period}日"),
            main_net_inflow=float(subset["main_net_inflow"].sum()),
            main_net_ratio=float(subset.iloc[0]["main_net_ratio"]),
            super_large_net_inflow=float(subset["super_large_net_inflow"].sum()),
            large_net_inflow=float(subset["large_net_inflow"].sum()),
            medium_net_inflow=float(subset["medium_net_inflow"].sum()),
            small_net_inflow=float(subset["small_net_inflow"].sum()),
        )
        summaries.append(summary)

    return summaries


def analyze_trend(df: pd.DataFrame, lookback: int = 10) -> FundFlowTrend:
    """
    分析资金流向趋势

    Args:
        df: 资金流向数据
        lookback: 回看天数

    Returns:
        资金流向趋势
    """
    if len(df) < lookback:
        lookback = len(df)

    subset = df.head(lookback)

    # 计算连续流入/流出天数
    consecutive_days = 0
    for _, row in subset.iterrows():
        if row["main_net_inflow"] > 0:
            if consecutive_days >= 0:
                consecutive_days += 1
            else:
                break
        elif row["main_net_inflow"] < 0:
            if consecutive_days <= 0:
                consecutive_days -= 1
            else:
                break
        else:
            break

    # 计算日均净流入
    avg_daily_inflow = float(subset["main_net_inflow"].mean())

    # 判断趋势
    total_inflow = subset["main_net_inflow"].sum()
    positive_days = (subset["main_net_inflow"] > 0).sum()
    negative_days = (subset["main_net_inflow"] < 0).sum()

    if positive_days >= lookback * 0.7:
        trend = "持续流入"
        description = f"近{lookback}日中有{positive_days}日主力资金净流入，资金持续看好"
    elif negative_days >= lookback * 0.7:
        trend = "持续流出"
        description = f"近{lookback}日中有{negative_days}日主力资金净流出，资金持续撤离"
    else:
        trend = "震荡"
        description = f"近{lookback}日资金流向波动较大，流入{positive_days}日，流出{negative_days}日"

    return FundFlowTrend(
        trend=trend,
        description=description,
        consecutive_days=consecutive_days,
        avg_daily_inflow=avg_daily_inflow,
    )


def analyze_price_correlation(df: pd.DataFrame, lookback: int = 10) -> PriceCorrelation:
    """
    分析资金与价格关联

    Args:
        df: 资金流向数据
        lookback: 回看天数

    Returns:
        价格关联分析
    """
    if len(df) < lookback:
        lookback = len(df)

    subset = df.head(lookback)

    # 计算相关性
    main_inflow = subset["main_net_inflow"]
    pct_change = subset["pct_change"]

    # 简单判断：资金流入时是否上涨，流出时是否下跌
    same_direction = 0
    for _, row in subset.iterrows():
        if (row["main_net_inflow"] > 0 and row["pct_change"] > 0) or (
            row["main_net_inflow"] < 0 and row["pct_change"] < 0
        ):
            same_direction += 1

    correlation_ratio = same_direction / lookback

    if correlation_ratio >= 0.7:
        correlation = "资金推动"
        description = f"近{lookback}日中{same_direction}日资金与价格同向，股价受资金推动明显"
    elif correlation_ratio <= 0.3:
        correlation = "资金背离"
        description = f"近{lookback}日资金与价格走势背离，需关注转折信号"
    else:
        correlation = "无明显关联"
        description = f"近{lookback}日资金与价格关联性一般"

    return PriceCorrelation(correlation=correlation, description=description)


def process(code: str, periods: list[int] = None, lookback: int = 10) -> FundFlowResult:
    """
    处理个股资金流向分析

    Args:
        code: 股票代码
        periods: 汇总周期
        lookback: 趋势分析回看天数

    Returns:
        分析结果
    """
    if periods is None:
        periods = [1, 5, 10, 20]

    # 获取数据
    df = fetch_fund_flow(code)

    if df.empty:
        raise ValueError(f"未找到股票 {code} 的资金流向数据")

    # 计算各项分析
    summaries = calculate_summaries(df, periods)
    trend = analyze_trend(df, lookback)
    price_correlation = analyze_price_correlation(df, lookback)

    # 构建结果
    latest = df.iloc[0]
    pure_code, _ = normalize_stock_code(code)

    result = FundFlowResult(
        code=pure_code,
        name="",  # AKShare 接口不返回股票名称
        latest_date=str(latest["date"]),
        latest_price=float(latest["close"]),
        latest_change=float(latest["pct_change"]),
        summaries=summaries,
        trend=trend,
        price_correlation=price_correlation,
    )

    return result


def format_output(result: FundFlowResult) -> str:
    """
    格式化输出

    Args:
        result: 分析结果

    Returns:
        格式化的字符串
    """
    lines = []
    lines.append(f"=== {result.code} 资金流向分析 ===")
    lines.append(f"日期: {result.latest_date}  收盘: {result.latest_price:.2f}  涨跌: {result.latest_change:+.2f}%")
    lines.append("")

    # 资金流向汇总
    lines.append("--- 资金流向汇总 ---")
    for summary in result.summaries:
        net_inflow_yi = summary.main_net_inflow / 1e8  # 转换为亿
        sign = "+" if net_inflow_yi > 0 else ""
        lines.append(
            f"{summary.period}: 主力净流入 {sign}{net_inflow_yi:.2f}亿 ({summary.main_net_ratio:+.2f}%)"
        )
    lines.append("")

    # 趋势分析
    lines.append("--- 资金趋势 ---")
    lines.append(f"趋势: {result.trend.trend}")
    lines.append(f"分析: {result.trend.description}")
    if result.trend.consecutive_days > 0:
        lines.append(f"连续流入: {result.trend.consecutive_days} 日")
    elif result.trend.consecutive_days < 0:
        lines.append(f"连续流出: {abs(result.trend.consecutive_days)} 日")
    lines.append("")

    # 价格关联
    lines.append("--- 资金与价格关联 ---")
    lines.append(f"关联性: {result.price_correlation.correlation}")
    lines.append(f"分析: {result.price_correlation.description}")

    return "\n".join(lines)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="个股资金流向分析")
    parser.add_argument("code", help="股票代码（如 000001）")
    parser.add_argument("--periods", nargs="+", type=int, default=[1, 5, 10, 20], help="汇总周期")
    parser.add_argument("--lookback", type=int, default=10, help="趋势分析回看天数")
    parser.add_argument("--output", choices=["text", "json"], default="text", help="输出格式")
    parser.add_argument("--date", help="指定日期（仅用于保存路径）")
    return parser.parse_args()


def main():
    """主入口"""
    args = parse_args()

    try:
        result = process(args.code, args.periods, args.lookback)

        # 保存结果
        date_str = args.date or datetime.now().strftime("%Y-%m-%d")
        output_path = get_output_path(SKILL_NAME, PROCESSOR_NAME, date_str, ext="json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 转换为字典并保存
        result_dict = asdict(result)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)

        # 输出
        if args.output == "json":
            print(json.dumps(result_dict, ensure_ascii=False, indent=2))
        else:
            print(format_output(result))

        print(f"\n结果已保存: {output_path}")

    except Exception as e:
        print(f"错误: {e}")
        raise


if __name__ == "__main__":
    main()
