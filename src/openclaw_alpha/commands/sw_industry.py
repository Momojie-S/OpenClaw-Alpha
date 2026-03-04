# -*- coding: utf-8 -*-
"""A 股申万行业指数行情查询

该脚本用于获取 A 股申万行业指数的日行情数据，通过 Tushare Pro API 获取数据。
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any

import pandas as pd
import tushare as ts


def get_sw_industry_data(
    trade_date: str | None = None,
    level: str = "L3",
    top: int = 50,
    sort_by: str = "change_pct",
) -> dict[str, Any]:
    """获取申万行业指数行情数据.

    Args:
        trade_date: 交易日期 (YYYYMMDD)，默认为当日
        level: 行业层级 (L1/L2/L3)，默认 L3
        top: 返回前 N 个行业，默认 50
        sort_by: 排序字段，支持 change_pct（涨跌幅）、amount（成交额）、turnover_rate（换手率）

    Returns:
        包含行情数据的字典
    """
    # 检查 TUSHARE_TOKEN
    api_token = os.environ.get("TUSHARE_TOKEN")
    if not api_token:
        return {
            "success": False,
            "error": "TUSHARE_TOKEN 未配置，请在 .env 文件中设置",
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }

    try:
        # 初始化 Tushare Pro 客户端
        pro = ts.pro_api(api_token)

        # 处理日期参数
        if trade_date is None:
            trade_date = datetime.now().strftime("%Y%m%d")

        # 调用 Tushare API 获取申万行业指数日行情
        df: pd.DataFrame = pro.sw_daily(trade_date=trade_date)

        if df is None or df.empty:
            # 非交易日返回空数据
            return {
                "success": True,
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "trade_date": trade_date,
                "level": level,
                "count": 0,
                "data_source": "Tushare",
                "data": [],
            }

        # 行业层级筛选
        if level == "L1":
            # 一级行业：代码以 801 开头，且长度较短
            df = df[df["ts_code"].str.startswith("801")]
            # 进一步筛选：只保留 6 位代码对应的指数
            df = df[df["ts_code"].str[:6].str.len() == 6]
        elif level == "L2":
            # 二级行业：代码以 801 开头
            df = df[df["ts_code"].str.startswith("801")]
        elif level == "L3":
            # 三级行业：代码以 85 开头
            df = df[df["ts_code"].str.startswith("85")]

        # 确定排序字段
        sort_field_map = {
            "change_pct": "pct_change",
            "amount": "amount",
            "turnover_rate": "turnover_rate",  # 将在后面计算
        }
        sort_column = sort_field_map.get(sort_by, "pct_change")

        # 计算换手率 = 成交额 / 流通市值 * 100
        # amount: 千元, float_mv: 万元
        df["turnover_rate"] = df.apply(
            lambda row: (row["amount"] * 1000) / (row["float_mv"] * 10000) * 100
            if pd.notna(row["float_mv"]) and row["float_mv"] > 0
            else 0,
            axis=1,
        )

        # 按排序字段降序排列
        if sort_column in df.columns:
            df = df.sort_values(by=sort_column, ascending=False)

        # 取前 N 个
        df = df.head(top)

        # 构建结果数据
        data_list: list[dict[str, Any]] = []
        for idx, row in enumerate(df.itertuples(), start=1):
            # 字段映射和转换
            volume = getattr(row, "vol", 0) or 0
            amount = getattr(row, "amount", 0) or 0

            item = {
                "rank": idx,
                "board_code": str(getattr(row, "ts_code", "")),
                "board_name": str(getattr(row, "name", "")),
                "change_pct": round(float(getattr(row, "pct_change", 0) or 0), 2),
                "close": round(float(getattr(row, "close", 0) or 0), 2),
                "volume": round(float(volume) / 10000, 2),  # 手 -> 万手
                "amount": round(float(amount) * 1000 / 100000000, 2),  # 千元 -> 亿元
                "turnover_rate": round(float(getattr(row, "turnover_rate", 0) or 0), 2),
                "float_mv": round(float(getattr(row, "float_mv", 0) or 0) / 10000, 2),  # 万元 -> 亿
                "total_mv": round(float(getattr(row, "total_mv", 0) or 0) / 10000, 2),  # 万元 -> 亿
                "pe": round(float(getattr(row, "pe", 0) or 0), 2),
                "pb": round(float(getattr(row, "pb", 0) or 0), 2),
            }
            data_list.append(item)

        return {
            "success": True,
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "trade_date": trade_date,
            "level": level,
            "count": len(data_list),
            "data_source": "Tushare",
            "data": data_list,
        }

    except Exception as e:
        error_msg = str(e)
        # 检测积分不足的情况
        if "积分" in error_msg or "权限" in error_msg:
            error_msg = "Tushare 积分不足，sw_daily 需 120 积分"
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }


def main() -> None:
    """CLI 入口."""
    parser = argparse.ArgumentParser(description="A 股申万行业指数行情")
    parser.add_argument(
        "--date", type=str, default=None, help="交易日期 (YYYYMMDD)，默认当日"
    )
    parser.add_argument(
        "--level",
        type=str,
        default="L3",
        choices=["L1", "L2", "L3"],
        help="行业层级: L1(一级), L2(二级), L3(三级) (默认: L3)",
    )
    parser.add_argument(
        "--top", type=int, default=50, help="返回前 N 个行业 (默认: 50)"
    )
    parser.add_argument(
        "--sort",
        type=str,
        default="change_pct",
        choices=["change_pct", "amount", "turnover_rate"],
        help="排序字段: change_pct(涨跌幅), amount(成交额), turnover_rate(换手率) (默认: change_pct)",
    )
    args = parser.parse_args()

    result = get_sw_industry_data(
        trade_date=args.date, level=args.level, top=args.top, sort_by=args.sort
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 如果失败，返回非零退出码
    if not result.get("success", False):
        sys.exit(1)


if __name__ == "__main__":
    main()
