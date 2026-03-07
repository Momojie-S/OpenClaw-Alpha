# -*- coding: utf-8 -*-
"""选股筛选器 Processor"""

import argparse
import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from openclaw_alpha.core.processor_utils import get_output_path

from ..stock_spot_fetcher import StockSpot, fetch

logger = logging.getLogger(__name__)

# Skill 和 Processor 名称
SKILL_NAME = "stock_screener"
PROCESSOR_NAME = "screener"

# 预设筛选策略
STRATEGIES: dict[str, dict[str, Any]] = {
    "volume_breakout": {
        "name": "放量突破",
        "desc": "涨幅 > 3%，换手率 > 5%，成交额 > 2 亿",
        "conditions": {
            "change_min": 3.0,
            "turnover_min": 5.0,
            "amount_min": 2.0,
        },
    },
    "pullback": {
        "name": "缩量回调",
        "desc": "涨幅 -5% ~ 0%，换手率 < 3%",
        "conditions": {
            "change_min": -5.0,
            "change_max": 0.0,
            "turnover_max": 3.0,
        },
    },
    "leader": {
        "name": "龙头股",
        "desc": "涨幅 > 5%，成交额 > 10 亿，市值 > 100 亿",
        "conditions": {
            "change_min": 5.0,
            "amount_min": 10.0,
            "cap_min": 100.0,
        },
    },
    "small_active": {
        "name": "小盘活跃",
        "desc": "换手率 > 8%，市值 < 50 亿",
        "conditions": {
            "turnover_min": 8.0,
            "cap_max": 50.0,
        },
    },
    "blue_chip": {
        "name": "低估蓝筹",
        "desc": "市值 > 500 亿，换手率 < 2%",
        "conditions": {
            "cap_min": 500.0,
            "turnover_max": 2.0,
        },
    },
}


@dataclass
class FilterConditions:
    """筛选条件"""

    change_min: float | None = None  # 涨幅下限（%）
    change_max: float | None = None  # 涨幅上限（%）
    turnover_min: float | None = None  # 换手下限（%）
    turnover_max: float | None = None  # 换手上限（%）
    amount_min: float | None = None  # 成交额下限（亿）
    amount_max: float | None = None  # 成交额上限（亿）
    cap_min: float | None = None  # 市值下限（亿）
    cap_max: float | None = None  # 市值上限（亿）
    price_min: float | None = None  # 价格下限（元）
    price_max: float | None = None  # 价格上限（元）

    @classmethod
    def from_strategy(cls, strategy_name: str) -> "FilterConditions | None":
        """从预设策略创建条件"""
        if strategy_name not in STRATEGIES:
            return None
        conditions = STRATEGIES[strategy_name]["conditions"]
        return cls(**conditions)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ScreenResult:
    """筛选结果"""

    code: str
    name: str
    change_pct: float
    turnover_rate: float
    amount: float
    price: float
    market_cap: float


class ScreenerProcessor:
    """选股筛选器"""

    def filter(self, spots: list[StockSpot], conditions: FilterConditions) -> list[StockSpot]:
        """
        按条件筛选股票

        Args:
            spots: 全市场股票行情
            conditions: 筛选条件

        Returns:
            筛选结果
        """
        result = []
        for spot in spots:
            if self._match(spot, conditions):
                result.append(spot)
        return result

    def _match(self, spot: StockSpot, conditions: FilterConditions) -> bool:
        """
        检查股票是否匹配条件

        Args:
            spot: 股票行情
            conditions: 筛选条件

        Returns:
            是否匹配
        """
        # 涨跌幅
        if conditions.change_min is not None and spot.change_pct < conditions.change_min:
            return False
        if conditions.change_max is not None and spot.change_pct > conditions.change_max:
            return False

        # 换手率
        if conditions.turnover_min is not None and spot.turnover_rate < conditions.turnover_min:
            return False
        if conditions.turnover_max is not None and spot.turnover_rate > conditions.turnover_max:
            return False

        # 成交额
        if conditions.amount_min is not None and spot.amount < conditions.amount_min:
            return False
        if conditions.amount_max is not None and spot.amount > conditions.amount_max:
            return False

        # 市值
        if conditions.cap_min is not None and spot.market_cap < conditions.cap_min:
            return False
        if conditions.cap_max is not None and spot.market_cap > conditions.cap_max:
            return False

        # 价格
        if conditions.price_min is not None and spot.price < conditions.price_min:
            return False
        if conditions.price_max is not None and spot.price > conditions.price_max:
            return False

        return True

    def sort_by_change(self, spots: list[StockSpot], descending: bool = True) -> list[StockSpot]:
        """按涨跌幅排序"""
        return sorted(spots, key=lambda x: x.change_pct, reverse=descending)

    def to_screen_results(self, spots: list[StockSpot]) -> list[ScreenResult]:
        """转换为输出格式"""
        return [
            ScreenResult(
                code=s.code,
                name=s.name,
                change_pct=round(s.change_pct, 2),
                turnover_rate=round(s.turnover_rate, 2),
                amount=s.amount,
                price=round(s.price, 2),
                market_cap=s.market_cap,
            )
            for s in spots
        ]


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="选股筛选器")

    # 策略模式
    parser.add_argument(
        "--strategy",
        choices=list(STRATEGIES.keys()),
        help="使用预设策略筛选",
    )

    # 自定义条件
    parser.add_argument("--change-min", type=float, help="涨幅下限（%）")
    parser.add_argument("--change-max", type=float, help="涨幅上限（%）")
    parser.add_argument("--turnover-min", type=float, help="换手下限（%）")
    parser.add_argument("--turnover-max", type=float, help="换手上限（%）")
    parser.add_argument("--amount-min", type=float, help="成交额下限（亿）")
    parser.add_argument("--amount-max", type=float, help="成交额上限（亿）")
    parser.add_argument("--cap-min", type=float, help="市值下限（亿）")
    parser.add_argument("--cap-max", type=float, help="市值上限（亿）")
    parser.add_argument("--price-min", type=float, help="价格下限（元）")
    parser.add_argument("--price-max", type=float, help="价格上限（元）")

    # 输出控制
    parser.add_argument("--top-n", type=int, default=20, help="返回 Top N 结果（默认 20）")
    parser.add_argument(
        "--sort",
        choices=["change", "turnover", "amount", "cap"],
        default="change",
        help="排序字段（默认 change）",
    )
    parser.add_argument(
        "--asc",
        action="store_true",
        help="升序排序（默认降序）",
    )
    parser.add_argument(
        "--list-strategies",
        action="store_true",
        help="列出所有预设策略",
    )

    return parser.parse_args()


def list_strategies():
    """列出所有预设策略"""
    print("可用的筛选策略：\n")
    for key, info in STRATEGIES.items():
        print(f"  {key}")
        print(f"    名称：{info['name']}")
        print(f"    条件：{info['desc']}")
        print()


async def process(
    strategy: str | None = None,
    conditions: FilterConditions | None = None,
    top_n: int = 20,
    sort_by: str = "change",
    ascending: bool = False,
    date: str | None = None,
) -> dict[str, Any]:
    """
    执行筛选

    Args:
        strategy: 预设策略名
        conditions: 自定义条件
        top_n: 返回 Top N
        sort_by: 排序字段
        ascending: 是否升序
        date: 日期

    Returns:
        筛选结果
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # 确定筛选条件
    if strategy:
        conditions = FilterConditions.from_strategy(strategy)
        if conditions is None:
            raise ValueError(f"未知策略: {strategy}")
    elif conditions is None:
        # 默认条件：涨幅 > 0
        conditions = FilterConditions(change_min=0.0)

    # 获取数据
    spots = await fetch()
    if not spots:
        return {
            "date": date,
            "error": "获取数据失败，可能非交易日或数据未更新",
            "total_matched": 0,
            "results": [],
        }

    # 筛选
    processor = ScreenerProcessor()
    matched = processor.filter(spots, conditions)

    # 排序
    sort_key_map = {
        "change": lambda x: x.change_pct,
        "turnover": lambda x: x.turnover_rate,
        "amount": lambda x: x.amount,
        "cap": lambda x: x.market_cap,
    }
    sort_key = sort_key_map.get(sort_by, lambda x: x.change_pct)
    matched = sorted(matched, key=sort_key, reverse=not ascending)

    # Top N
    top_matched = matched[:top_n]

    # 转换输出
    results = processor.to_screen_results(top_matched)
    results_dict = [asdict(r) for r in results]

    # 输出信息
    output = {
        "date": date,
        "strategy": strategy,
        "conditions": conditions.to_dict() if not strategy else None,
        "total_matched": len(matched),
        "showing": len(top_matched),
        "results": results_dict,
    }

    # 保存到文件
    output_path = get_output_path(SKILL_NAME, PROCESSOR_NAME, date, ext="json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return output


def main():
    """主入口"""
    args = parse_args()

    # 列出策略
    if args.list_strategies:
        list_strategies()
        return

    # 构建条件
    conditions = None
    if not args.strategy:
        conditions = FilterConditions(
            change_min=args.change_min,
            change_max=args.change_max,
            turnover_min=args.turnover_min,
            turnover_max=args.turnover_max,
            amount_min=args.amount_min,
            amount_max=args.amount_max,
            cap_min=args.cap_min,
            cap_max=args.cap_max,
            price_min=args.price_min,
            price_max=args.price_max,
        )

    # 执行筛选
    result = asyncio.run(
        process(
            strategy=args.strategy,
            conditions=conditions,
            top_n=args.top_n,
            sort_by=args.sort,
            ascending=args.asc,
        )
    )

    # 输出
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
