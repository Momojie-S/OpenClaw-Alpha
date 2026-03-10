# -*- coding: utf-8 -*-
"""涨停追踪 Fetcher - 入口类"""

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path

from openclaw_alpha.core.fetcher import Fetcher
# 导入数据源以触发注册
import openclaw_alpha.data_sources  # noqa: F401

from .models import LimitUpResult, LimitUpType
from .akshare import LimitUpFetcherAkshare
from .tushare import LimitUpFetcherTushare


class LimitUpFetcher(Fetcher):
    """涨停追踪 Fetcher - 入口类"""

    name = "limit_up"

    def __init__(self):
        super().__init__()
        # 注册实现（优先级：Tushare > AKShare）
        self.register(LimitUpFetcherTushare(), priority=20)
        self.register(LimitUpFetcherAkshare(), priority=10)

    async def fetch(
        self,
        date: str,
        limit_type: LimitUpType = LimitUpType.LIMIT_UP,
    ) -> LimitUpResult:
        """
        获取涨停数据

        Args:
            date: 交易日期 (YYYY-MM-DD 或 YYYYMMDD)
            limit_type: 涨停类型

        Returns:
            LimitUpResult
        """
        # 标准化日期格式
        if "-" in date:
            date_fmt = date.replace("-", "")
        else:
            date_fmt = date

        # 选择可用实现
        method, errors = self._select_available()
        if method is None:
            from openclaw_alpha.core.exceptions import NoAvailableMethodError
            checked = [m.name for m in self._methods]
            raise NoAvailableMethodError(self.name, checked, errors)

        # 调用实现
        result = await method.fetch(date_fmt, limit_type)

        # 计算连板统计
        continuous_stat: dict[int, int] = {}
        for item in result.items:
            c = item.continuous
            # 4连板以上归为 4+
            key = c if c < 4 else 4
            continuous_stat[key] = continuous_stat.get(key, 0) + 1

        result.continuous_stat = continuous_stat

        return result


async def fetch(
    date: str | None = None,
    limit_type: LimitUpType = LimitUpType.LIMIT_UP,
) -> LimitUpResult:
    """
    获取涨停数据

    Args:
        date: 交易日期，默认今天
        limit_type: 涨停类型

    Returns:
        LimitUpResult
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    fetcher = LimitUpFetcher()
    return await fetcher.fetch(date, limit_type)


def format_output(result: LimitUpResult, top_n: int = 20, min_continuous: int = 1) -> str:
    """格式化输出"""
    # 筛选连板数
    items = [item for item in result.items if item.continuous >= min_continuous]

    # 按连板数排序
    items.sort(key=lambda x: (x.continuous, x.change_pct), reverse=True)

    # 限制数量
    display_items = items[:top_n]

    # 类型名称
    type_names = {
        LimitUpType.LIMIT_UP: "涨停",
        LimitUpType.LIMIT_DOWN: "跌停",
        LimitUpType.BROKEN: "炸板",
        LimitUpType.PREVIOUS: "昨日涨停",
    }

    lines = [
        f"{type_names.get(result.limit_type, '涨停')}股池 ({result.date}) - 共 {result.total} 只",
        "=" * 70,
    ]

    # 连板统计
    if result.continuous_stat:
        stat_parts = []
        for c in sorted(result.continuous_stat.keys()):
            count = result.continuous_stat[c]
            label = f"{c}+板" if c >= 4 else f"{c}板" if c > 1 else "首板"
            stat_parts.append(f"{label} {count}")
        lines.append("连板统计: " + " | ".join(stat_parts))
        lines.append("")

    if not display_items:
        lines.append("无符合条件的股票")
        return "\n".join(lines)

    lines.extend([
        f"Top {len(display_items)} 连板股:",
        "-" * 70,
        f"{'代码':<8} {'名称':<10} {'连板':>4} {'封板时间':>10} {'炸板':>4} {'流通市值(亿)':>12} {'所属行业':<10}",
        "-" * 70,
    ])

    for item in display_items:
        lines.append(
            f"{item.code:<8} {item.name:<10} {item.continuous:>4} "
            f"{item.first_limit_time:>10} {item.limit_times:>4} "
            f"{item.float_mv:>12.2f} {item.industry:<10}"
        )

    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description="涨停追踪")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="交易日期")
    parser.add_argument(
        "--type",
        choices=["limit_up", "limit_down", "broken", "previous"],
        default="limit_up",
        help="类型: limit_up(涨停), limit_down(跌停), broken(炸板), previous(昨日涨停)",
    )
    parser.add_argument("--min-continuous", type=int, default=1, help="最小连板数")
    parser.add_argument("--top-n", type=int, default=20, help="返回数量")
    return parser.parse_args()


async def main():
    args = parse_args()

    limit_type = LimitUpType(args.type)
    result = await fetch(args.date, limit_type)

    # 输出格式化结果
    print(format_output(result, args.top_n, args.min_continuous))

    # 保存完整数据到文件
    output_dir = Path.cwd() / ".openclaw_alpha" / "limit_up_tracker" / args.date
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{args.type}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

    print(f"\n完整数据已保存到: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
