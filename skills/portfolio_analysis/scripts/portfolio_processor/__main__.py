# -*- coding: utf-8 -*-
"""持仓分析 Processor 主程序"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目根目录到路径（支持直接执行）
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    skills_dir = project_root / "skills"
    if str(skills_dir) not in sys.path:
        sys.path.insert(0, str(skills_dir))

    # 注册数据源

from openclaw_alpha.core.processor_utils import get_output_path

from portfolio_analysis.scripts.industry_fetcher import fetch as fetch_industry
from portfolio_analysis.scripts.portfolio_processor.portfolio_processor import (
    PortfolioProcessor,
    PortfolioResult,
)

# 复用 stock_screener 的 StockSpotFetcher
from stock_screener.scripts.stock_spot_fetcher import fetch as fetch_spot

logger = logging.getLogger(__name__)

SKILL_NAME = "portfolio_analysis"
PROCESSOR_NAME = "portfolio"


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="持仓分析")
    parser.add_argument(
        "--holdings",
        type=str,
        help='持仓字符串，格式: "000001:1000:12.5,600000:500:8.2"',
    )
    parser.add_argument("--file", type=str, help="持仓 JSON 文件路径")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"))
    return parser.parse_args()


def load_holdings_from_file(file_path: str) -> list[dict[str, Any]]:
    """
    从 JSON 文件加载持仓

    Args:
        file_path: 文件路径

    Returns:
        持仓列表
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("holdings", [])


async def process(holdings_input: list[dict[str, Any]], date: str) -> PortfolioResult:
    """
    执行持仓分析

    Args:
        holdings_input: 持仓输入列表
        date: 日期

    Returns:
        分析结果
    """
    processor = PortfolioProcessor()

    # 提取股票代码
    codes = [h["code"] for h in holdings_input]

    # 获取实时行情
    logger.info(f"正在获取 {len(codes)} 只股票的行情数据...")
    spots = await fetch_spot()
    stock_data = {}
    for spot in spots:
        stock_data[spot.code] = {
            "price": spot.price,
            "name": spot.name,
            "change_pct": spot.change_pct,
            "market_cap": spot.market_cap,
        }

    # 获取行业信息
    logger.info(f"正在获取 {len(codes)} 只股票的行业信息...")
    industry_info = await fetch_industry(codes)

    # 合并行业信息
    for code, info in industry_info.items():
        if code in stock_data:
            stock_data[code]["industry"] = info.industry

    # 执行分析
    result = processor.process(holdings_input, stock_data)

    return result


async def main():
    """主函数"""
    args = parse_args()

    # 解析持仓
    holdings_input = []
    if args.holdings:
        processor = PortfolioProcessor()
        holdings_input = processor.parse_holdings_string(args.holdings)
    elif args.file:
        holdings_input = load_holdings_from_file(args.file)
    else:
        print("错误: 请使用 --holdings 或 --file 指定持仓")
        sys.exit(1)

    if not holdings_input:
        print("错误: 未找到有效持仓")
        sys.exit(1)

    print(f"分析 {len(holdings_input)} 只股票的持仓...")

    try:
        result = await process(holdings_input, args.date)

        # 输出摘要
        processor = PortfolioProcessor()
        summary = processor.format_summary(result)
        print("\n" + summary)

        # 保存完整结果
        output_path = get_output_path(SKILL_NAME, PROCESSOR_NAME, args.date, ext="json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result_dict = processor.to_dict(result)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)

        print(f"\n完整结果已保存到: {output_path}")

    except Exception as e:
        print(f"分析失败: {e}")
        logger.exception("持仓分析失败")
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main())
