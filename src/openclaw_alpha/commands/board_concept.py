# -*- coding: utf-8 -*-
"""A 股概念板块实时行情查询

该脚本用于获取 A 股市场所有概念板块的实时行情数据，通过 AKShare 调用东方财富数据源。
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from typing import Any

import akshare as ak
import pandas as pd

from openclaw_alpha.core.exceptions import NoAvailableFetcherError
from openclaw_alpha.core.fetcher_registry import FetcherRegistry
from openclaw_alpha.fetchers.concept_board import (
    ConceptBoardAkshareFetcher,
    ConceptBoardFetchParams,
)


def get_concept_board_data(
    top: int = 20, sort_by: str = "change_pct"
) -> dict[str, Any]:
    """获取概念板块行情数据.

    使用 Fetcher 模式获取数据，保持向后兼容。

    Args:
        top: 返回前 N 个板块，默认 20
        sort_by: 排序字段，支持 change_pct（涨跌幅）、amount（成交额）、volume（成交量）、turnover（换手率）

    Returns:
        包含行情数据的字典
    """
    return asyncio.run(_get_concept_board_data_async(top, sort_by))


async def _get_concept_board_data_async(
    top: int, sort_by: str
) -> dict[str, Any]:
    """获取概念板块行情数据（异步实现）"""
    try:
        # 注册 Akshare Fetcher（如果尚未注册）
        registry = FetcherRegistry.get_instance()
        try:
            registry.get("akshare_concept")
        except KeyError:
            registry.register(ConceptBoardAkshareFetcher())

        # 使用 FetcherRegistry 获取可用的 Fetcher
        fetcher = registry.get_available("concept_board")
        if not fetcher:
            raise NoAvailableFetcherError("concept_board")

        params = ConceptBoardFetchParams(
            top=top,
            sort_by=sort_by,
        )
        result = await fetcher[0].fetch(params)

        # 转换为命令返回格式
        items = []
        for item in result.items:
            items.append(
                {
                    "rank": item.rank,
                    "board_code": item.board_code,
                    "board_name": item.board_name,
                    "price": item.price,
                    "change_pct": item.change_pct,
                    "change": item.change,
                    "volume": item.volume,
                    "amount": item.amount,
                    "turnover_rate": item.turnover_rate,
                    "up_count": item.up_count,
                    "down_count": item.down_count,
                    "leader_name": item.leader_name,
                    "leader_change": item.leader_change,
                    "total_mv": item.total_mv,
                    "data_source": result.data_source,
                }
            )

        return {
            "success": True,
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "trade_date": result.trade_date,
            "count": len(items),
            "data_source": result.data_source,
            "data": items,
        }

    except NoAvailableFetcherError:
        raise
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
