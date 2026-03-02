# -*- coding: utf-8 -*-
"""A 股概念板块实时行情查询

该脚本用于获取 A 股市场所有概念板块的实时行情数据，通过 AKShare 调用东方财富数据源。
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any

import akshare as ak
import pandas as pd


def get_concept_board_data(
    top: int = 20, sort_by: str = "change_pct"
) -> dict[str, Any]:
    """获取概念板块行情数据.

    Args:
        top: 返回前 N 个板块，默认 20
        sort_by: 排序字段，支持 change_pct（涨跌幅）、amount（成交额）、volume（成交量）、turnover（换手率）

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
        # 调用 AKShare API 获取概念板块数据（东方财富数据源）
        df: pd.DataFrame = ak.stock_board_concept_name_em()

        if df is None or df.empty:
            return {
                "success": False,
                "error": "未获取到概念板块数据",
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            }

        # 东方财富返回字段映射：
        # 板块代码, 板块名称, 最新价, 涨跌幅, 涨跌额, 成交量, 成交额, 换手率, 上涨家数, 下跌家数, 领涨股票, 领涨涨幅, 总市值

        # 确定排序字段
        sort_field_map = {
            "change_pct": "涨跌幅",
            "amount": "总成交额",
            "volume": "总成交量",
            "turnover": "换手率",
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
                "board_code": str(getattr(row, "板块代码", "")),
                "board_name": str(getattr(row, "板块名称", "")),
                "price": round(float(getattr(row, "最新价", 0) or 0), 2),
                "change_pct": round(float(getattr(row, "涨跌幅", 0) or 0), 2),
                "change": round(float(getattr(row, "涨跌额", 0) or 0), 2),
                "volume": round(float(getattr(row, "总成交量", 0) or 0), 2),
                "amount": round(float(getattr(row, "总成交额", 0) or 0), 2),
                "turnover_rate": round(float(getattr(row, "换手率", 0) or 0), 2),
                "up_count": int(getattr(row, "上涨家数", 0) or 0),
                "down_count": int(getattr(row, "下跌家数", 0) or 0),
                "leader_name": str(getattr(row, "领涨股票", "")),
                "leader_change": round(
                    float(getattr(row, "领涨股票_涨跌幅", 0) or 0), 2
                ),
                "total_mv": round(float(getattr(row, "总市值", 0) or 0), 2),
            }
            data_list.append(item)

        # 获取交易日期（当天）
        trade_date = datetime.now().strftime("%Y-%m-%d")

        return {
            "success": True,
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "trade_date": trade_date,
            "count": len(data_list),
            "data_source": "东方财富",
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
    parser = argparse.ArgumentParser(description="A 股概念板块实时行情")
    parser.add_argument(
        "--top", type=int, default=20, help="返回前 N 个板块 (默认: 20)"
    )
    parser.add_argument(
        "--sort",
        type=str,
        default="change_pct",
        choices=["change_pct", "amount", "volume", "turnover"],
        help="排序字段: change_pct(涨跌幅), amount(成交额), volume(成交量), turnover(换手率) (默认: change_pct)",
    )
    args = parser.parse_args()

    result = get_concept_board_data(top=args.top, sort_by=args.sort)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 如果失败，返回非零退出码
    if not result.get("success", False):
        sys.exit(1)


if __name__ == "__main__":
    main()
