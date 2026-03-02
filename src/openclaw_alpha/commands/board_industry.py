# -*- coding: utf-8 -*-
"""A 股行业板块实时行情查询

该脚本用于获取 A 股市场所有行业板块的实时行情数据，通过 AKShare 调用同花顺数据源。
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any

import akshare as ak
import pandas as pd


def get_industry_board_data(
    top: int = 20, sort_by: str = "change_pct"
) -> dict[str, Any]:
    """获取行业板块行情数据.

    Args:
        top: 返回前 N 个板块，默认 20
        sort_by: 排序字段，支持 change_pct（涨跌幅）、amount（成交额）、net_inflow（净流入）

    Returns:
        包含行情数据的字典，格式如下：
        {
            "success": true,
            "timestamp": "2026-03-02T10:30:00",
            "trade_date": "2026-03-02",
            "count": 20,
            "data": [...]
        }
    """
    try:
        # 调用 AKShare API 获取行业板块数据（同花顺数据源）
        # stock_board_industry_summary_ths 返回同花顺行业板块行情汇总
        df: pd.DataFrame = ak.stock_board_industry_summary_ths()

        if df is None or df.empty:
            return {
                "success": False,
                "error": "未获取到行业板块数据",
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            }

        # 同花顺返回字段映射：
        # 序号, 板块, 涨跌幅, 总成交量, 总成交额, 净流入, 上涨家数, 下跌家数, 均价, 领涨股, 领涨股-最新价, 领涨股-涨跌幅

        # 确定排序字段
        sort_field_map = {
            "change_pct": "涨跌幅",
            "amount": "总成交额",
            "net_inflow": "净流入",
        }
        sort_column = sort_field_map.get(sort_by, "涨跌幅")

        # 按排序字段降序排列
        if sort_column in df.columns:
            # 处理可能的字符串类型数据
            df[sort_column] = pd.to_numeric(df[sort_column], errors="coerce")
            df = df.sort_values(by=sort_column, ascending=False)

        # 取前 N 个
        df = df.head(top)

        # 构建结果数据
        data_list: list[dict[str, Any]] = []
        for idx, row in enumerate(df.itertuples(), start=1):
            item = {
                "rank": idx,
                "board_name": str(getattr(row, "板块", "")),
                "change_pct": round(float(getattr(row, "涨跌幅", 0) or 0), 2),
                "volume": round(float(getattr(row, "总成交量", 0) or 0), 2),  # 万手
                "amount": round(float(getattr(row, "总成交额", 0) or 0), 2),  # 亿
                "net_inflow": round(float(getattr(row, "净流入", 0) or 0), 2),  # 亿
                "up_count": int(getattr(row, "上涨家数", 0) or 0),
                "down_count": int(getattr(row, "下跌家数", 0) or 0),
                "leader_name": str(getattr(row, "领涨股", "")),
                "leader_change": round(
                    float(getattr(row, "领涨股_涨跌幅", 0) or 0), 2
                ),
            }
            data_list.append(item)

        # 获取交易日期（当天）
        trade_date = datetime.now().strftime("%Y-%m-%d")

        return {
            "success": True,
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "trade_date": trade_date,
            "count": len(data_list),
            "data_source": "同花顺",
            "data": data_list,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }


def main() -> None:
    """CLI 入口."""
    parser = argparse.ArgumentParser(description="A 股行业板块实时行情")
    parser.add_argument(
        "--top", type=int, default=20, help="返回前 N 个板块 (默认: 20)"
    )
    parser.add_argument(
        "--sort",
        type=str,
        default="change_pct",
        choices=["change_pct", "amount", "net_inflow"],
        help="排序字段: change_pct(涨跌幅), amount(成交额), net_inflow(净流入) (默认: change_pct)",
    )
    args = parser.parse_args()

    result = get_industry_board_data(top=args.top, sort_by=args.sort)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 如果失败，返回非零退出码
    if not result.get("success", False):
        sys.exit(1)


if __name__ == "__main__":
    main()
