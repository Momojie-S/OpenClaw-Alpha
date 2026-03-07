# -*- coding: utf-8 -*-
"""个股分析 Processor"""

import argparse
import asyncio
import json
from datetime import datetime
from typing import Any

from openclaw_alpha.core.processor_utils import get_output_path
# 导入数据源模块以触发注册
from openclaw_alpha.data_sources import registry  # noqa: F401

from skills.stock_analysis.scripts.stock_fetcher import fetch


# 常量定义
SKILL_NAME = "stock-analysis"
PROCESSOR_NAME = "analysis"


class StockAnalysisProcessor:
    """个股分析 Processor

    获取单只股票的核心指标并给出分析结论。
    """

    def __init__(self):
        """初始化 Processor"""
        self.identifier = None
        self.date = None

    async def process(self, identifier: str, date: str = None) -> dict[str, Any]:
        """处理主流程

        Args:
            identifier: 股票代码或名称
            date: 日期（YYYY-MM-DD），默认最近交易日

        Returns:
            包含股票数据和分析结论的结果字典
        """
        self.identifier = identifier
        self.date = date or datetime.now().strftime("%Y-%m-%d")

        # 1. 获取股票数据
        stock_data = await self._fetch_data()

        if "error" in stock_data:
            return {
                "error": stock_data["error"],
                "identifier": identifier,
                "date": self.date,
            }

        # 2. 计算分析结论
        analysis = self._analyze(stock_data)

        # 3. 构建结果
        result = {
            **stock_data,
            "analysis": analysis,
        }

        # 4. 保存结果
        self._save_output(result)

        return result

    async def _fetch_data(self) -> dict:
        """获取股票数据

        Returns:
            股票数据字典
        """
        return await fetch(self.identifier, self.date)

    def _analyze(self, stock_data: dict) -> dict[str, str]:
        """分析股票数据

        Args:
            stock_data: 股票数据

        Returns:
            分析结论字典
        """
        analysis = {}

        # 活跃度分析
        turnover_rate = stock_data.get("volume", {}).get("turnover_rate", 0)
        if turnover_rate > 10:
            analysis["activity"] = "非常活跃"
        elif turnover_rate > 5:
            analysis["activity"] = "较活跃"
        elif turnover_rate > 2:
            analysis["activity"] = "正常"
        else:
            analysis["activity"] = "不活跃"

        # 涨跌分析
        pct_change = stock_data.get("price", {}).get("pct_change", 0)
        if pct_change > 5:
            analysis["trend"] = "大涨"
        elif pct_change > 2:
            analysis["trend"] = "上涨"
        elif pct_change < -5:
            analysis["trend"] = "大跌"
        elif pct_change < -2:
            analysis["trend"] = "下跌"
        else:
            analysis["trend"] = "持平"

        return analysis

    def _save_output(self, result: dict[str, Any]) -> None:
        """保存结果到文件

        Args:
            result: 结果数据
        """
        output_path = get_output_path(
            SKILL_NAME,
            PROCESSOR_NAME,
            self.date,
            ext="json",
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="个股分析")
    parser.add_argument(
        "identifier",
        help="股票代码或名称（如 000001 或 平安银行）",
    )
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="日期（YYYY-MM-DD，默认今天）",
    )
    return parser.parse_args()


async def main():
    """主入口"""
    args = parse_args()

    processor = StockAnalysisProcessor()
    result = await processor.process(
        identifier=args.identifier,
        date=args.date,
    )

    # 打印结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
