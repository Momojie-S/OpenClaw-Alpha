# -*- coding: utf-8 -*-
"""资金流向 Processor - 行业和概念板块资金流向分析"""

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

SKILL_NAME = "fund_flow_analysis"
PROCESSOR_NAME = "fund_flow"

# 时间周期映射
PERIOD_MAP = {
    "今日": "即时",
    "3日": "3日排行",
    "5日": "5日排行",
    "10日": "10日排行",
    "20日": "20日排行",
}


@dataclass
class FundFlowData:
    """资金流向数据"""
    rank: int           # 排名
    name: str           # 行业/概念名称
    index_value: float  # 行业指数
    change_pct: float   # 涨跌幅(%)
    inflow: float       # 流入资金(亿)
    outflow: float      # 流出资金(亿)
    net_amount: float   # 净额(亿)
    company_count: int  # 公司家数
    leading_stock: str  # 领涨股
    leading_change: float  # 领涨股涨跌幅(%)
    current_price: float   # 当前价

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="资金流向分析")
    parser.add_argument(
        "--type",
        choices=["industry", "concept"],
        default="industry",
        help="类型：industry(行业) / concept(概念)"
    )
    parser.add_argument(
        "--period",
        choices=["今日", "3日", "5日", "10日", "20日"],
        default="今日",
        help="时间周期"
    )
    parser.add_argument(
        "--min-net",
        type=float,
        default=None,
        help="最小净额过滤(亿)"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="返回 Top N"
    )
    parser.add_argument(
        "--sort-by",
        choices=["net", "change", "inflow"],
        default="net",
        help="排序字段：net(净额) / change(涨幅) / inflow(流入)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出文件路径"
    )
    return parser.parse_args()


def fetch_fund_flow(flow_type: str, period: str) -> pd.DataFrame:
    """获取资金流向数据

    Args:
        flow_type: 类型（industry/concept）
        period: 时间周期

    Returns:
        资金流向数据
    """
    symbol = PERIOD_MAP.get(period, "即时")
    
    if flow_type == "industry":
        df = ak.stock_fund_flow_industry(symbol=symbol)
    else:
        df = ak.stock_fund_flow_concept(symbol=symbol)
    
    return df


def transform_data(df: pd.DataFrame) -> list[FundFlowData]:
    """转换数据格式

    Args:
        df: 原始数据

    Returns:
        转换后的数据列表
    """
    result = []
    for _, row in df.iterrows():
        # 处理涨跌幅，去掉 % 符号
        change_pct = row.get("行业-涨跌幅", 0)
        if isinstance(change_pct, str):
            change_pct = float(change_pct.replace("%", ""))
        
        leading_change = row.get("领涨股-涨跌幅", 0)
        if isinstance(leading_change, str):
            leading_change = float(leading_change.replace("%", ""))
        
        data = FundFlowData(
            rank=int(row.get("序号", 0)),
            name=str(row.get("行业", "")),
            index_value=float(row.get("行业指数", 0)),
            change_pct=float(change_pct),
            inflow=float(row.get("流入资金", 0)),
            outflow=float(row.get("流出资金", 0)),
            net_amount=float(row.get("净额", 0)),
            company_count=int(row.get("公司家数", 0)),
            leading_stock=str(row.get("领涨股", "")),
            leading_change=float(leading_change),
            current_price=float(row.get("当前价", 0)),
        )
        result.append(data)
    
    return result


def process_data(
    data: list[FundFlowData],
    min_net: Optional[float] = None,
    sort_by: str = "net",
    top_n: int = 10,
) -> list[FundFlowData]:
    """处理数据：筛选、排序

    Args:
        data: 原始数据
        min_net: 最小净额过滤
        sort_by: 排序字段
        top_n: 返回数量

    Returns:
        处理后的数据
    """
    # 筛选
    if min_net is not None:
        data = [d for d in data if d.net_amount >= min_net]
    
    # 排序
    if sort_by == "net":
        data.sort(key=lambda x: x.net_amount, reverse=True)
    elif sort_by == "change":
        data.sort(key=lambda x: x.change_pct, reverse=True)
    elif sort_by == "inflow":
        data.sort(key=lambda x: x.inflow, reverse=True)
    
    # 返回 Top N，并更新排名
    result = data[:top_n]
    for i, d in enumerate(result, start=1):
        d.rank = i
    
    return result


def format_output(data: list[FundFlowData], flow_type: str, period: str) -> str:
    """格式化输出

    Args:
        data: 数据列表
        flow_type: 类型
        period: 时间周期

    Returns:
        格式化后的字符串
    """
    type_name = "行业" if flow_type == "industry" else "概念"
    
    lines = [
        f"{type_name}资金流向 ({period}) - Top {len(data)}",
        "=" * 60,
        f"{'排名':<4} {type_name:<10} {'净额(亿)':>10} {'涨幅(%)':>8} {'领涨股':<10}",
        "-" * 60,
    ]
    
    for d in data:
        change_sign = "+" if d.change_pct >= 0 else ""
        lines.append(
            f"{d.rank:<4} {d.name:<10} {d.net_amount:>10.2f} "
            f"{change_sign}{d.change_pct:>7.2f} {d.leading_stock:<10}"
        )
    
    return "\n".join(lines)


def save_to_file(
    data: list[FundFlowData],
    flow_type: str,
    period: str,
    output_path: Optional[str] = None,
) -> Path:
    """保存数据到文件

    Args:
        data: 数据列表
        flow_type: 类型
        period: 时间周期
        output_path: 指定输出路径

    Returns:
        保存的文件路径
    """
    if output_path:
        path = Path(output_path)
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        path = get_output_path(SKILL_NAME, PROCESSOR_NAME, date_str, ext="json")
    
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # 转换为可序列化的格式
    output_data = {
        "type": flow_type,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "count": len(data),
        "data": [d.to_dict() for d in data],
    }
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    return path


async def process():
    """主处理流程"""
    args = parse_args()
    
    # 获取数据
    df = fetch_fund_flow(args.type, args.period)
    
    # 转换数据
    all_data = transform_data(df)
    
    # 处理数据（筛选、排序、Top N）
    result_data = process_data(
        all_data,
        min_net=args.min_net,
        sort_by=args.sort_by,
        top_n=args.top_n,
    )
    
    # 保存完整数据
    output_path = save_to_file(
        result_data,
        args.type,
        args.period,
        args.output,
    )
    
    # 输出精简结果
    output = format_output(result_data, args.type, args.period)
    print(output)
    print(f"\n完整数据已保存: {output_path}")
    
    return result_data


def main():
    """入口函数"""
    asyncio.run(process())


if __name__ == "__main__":
    main()
