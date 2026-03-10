# -*- coding: utf-8 -*-
"""自选股监控 Processor"""

import argparse
import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

# 复用 stock_screener 的 StockSpotFetcher
from openclaw_alpha.skills.stock_screener.stock_spot_fetcher import StockSpot, fetch as fetch_spot

# 常量
SKILL_NAME = "watchlist_monitor"
PROCESSOR_NAME = "watchlist"
LIMIT_UP_THRESHOLD = 9.9  # 涨停阈值
LIMIT_DOWN_THRESHOLD = -9.9  # 跌停阈值


@dataclass
class WatchlistItem:
    """自选股条目"""

    code: str
    added_at: str
    note: str = ""


@dataclass
class WatchlistData:
    """自选股数据文件"""

    stocks: list[WatchlistItem]
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "stocks": [asdict(item) for item in self.stocks],
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WatchlistData":
        stocks = [WatchlistItem(**item) for item in data.get("stocks", [])]
        return cls(
            stocks=stocks,
            updated_at=data.get("updated_at", ""),
        )


@dataclass
class WatchlistSummary:
    """自选股分析摘要"""

    total: int
    up_count: int
    down_count: int
    flat_count: int
    avg_change: float
    best: StockSpot | None
    worst: StockSpot | None
    limit_up: list[StockSpot]
    limit_down: list[StockSpot]


class WatchlistManager:
    """自选股管理器"""

    def __init__(self, data_dir: Path | None = None):
        if data_dir is None:
            # 默认路径
            workspace = Path.cwd()
            data_dir = workspace / ".openclaw_alpha" / SKILL_NAME
        self.data_dir = data_dir
        self.data_file = data_dir / "watchlist.json"
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """确保数据目录存在"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> WatchlistData:
        """加载自选股列表"""
        if not self.data_file.exists():
            return WatchlistData(stocks=[], updated_at="")

        with open(self.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return WatchlistData.from_dict(data)

    def save(self, watchlist: WatchlistData):
        """保存自选股列表"""
        watchlist.updated_at = datetime.now().isoformat()
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(watchlist.to_dict(), f, ensure_ascii=False, indent=2)

    def add(self, codes: list[str], note: str = "") -> tuple[list[str], list[str]]:
        """
        添加自选股

        Args:
            codes: 股票代码列表
            note: 备注信息

        Returns:
            (添加成功的代码列表, 已存在的代码列表)
        """
        watchlist = self.load()
        existing_codes = {item.code for item in watchlist.stocks}

        added = []
        existing = []
        today = datetime.now().strftime("%Y-%m-%d")

        for code in codes:
            # 标准化代码（去掉前导零或补齐6位）
            normalized_code = self._normalize_code(code)
            if normalized_code in existing_codes:
                existing.append(normalized_code)
            else:
                watchlist.stocks.append(
                    WatchlistItem(code=normalized_code, added_at=today, note=note)
                )
                added.append(normalized_code)
                existing_codes.add(normalized_code)

        if added:
            self.save(watchlist)

        return added, existing

    def remove(self, codes: list[str]) -> list[str]:
        """
        移除自选股

        Returns:
            实际移除的代码列表
        """
        watchlist = self.load()
        codes_to_remove = {self._normalize_code(code) for code in codes}

        original_len = len(watchlist.stocks)
        watchlist.stocks = [
            item for item in watchlist.stocks if item.code not in codes_to_remove
        ]
        removed_count = original_len - len(watchlist.stocks)

        if removed_count > 0:
            self.save(watchlist)

        return [code for code in codes_to_remove if code in {item.code for item in watchlist.stocks[:removed_count] + [WatchlistItem(code=c, added_at="") for c in codes_to_remove]}][:removed_count]  # 简化：返回要移除的代码

    def clear(self):
        """清空自选股"""
        self.save(WatchlistData(stocks=[], updated_at=""))

    def list_codes(self) -> list[str]:
        """获取所有股票代码"""
        watchlist = self.load()
        return [item.code for item in watchlist.stocks]

    def _normalize_code(self, code: str) -> str:
        """标准化股票代码为6位"""
        code = code.strip()
        # 去掉可能的后缀如 .SZ, .SH
        if "." in code:
            code = code.split(".")[0]
        # 补齐6位
        return code.zfill(6)


class WatchlistProcessor:
    """自选股监控 Processor"""

    def __init__(self, manager: WatchlistManager | None = None):
        self.manager = manager or WatchlistManager()

    async def watch(self, top_n: int | None = None) -> list[StockSpot]:
        """
        获取自选股行情

        Args:
            top_n: 返回数量限制

        Returns:
            自选股行情列表
        """
        codes = self.manager.list_codes()
        if not codes:
            return []

        # 获取全市场行情
        all_stocks = await fetch_spot()

        # 筛选自选股
        code_set = set(codes)
        watchlist_stocks = [s for s in all_stocks if s.code in code_set]

        # 按涨跌幅排序
        watchlist_stocks.sort(key=lambda s: s.change_pct, reverse=True)

        if top_n is not None:
            watchlist_stocks = watchlist_stocks[:top_n]

        return watchlist_stocks

    def analyze(self, stocks: list[StockSpot]) -> WatchlistSummary:
        """
        分析自选股数据

        Args:
            stocks: 自选股行情列表

        Returns:
            分析摘要
        """
        if not stocks:
            return WatchlistSummary(
                total=0,
                up_count=0,
                down_count=0,
                flat_count=0,
                avg_change=0.0,
                best=None,
                worst=None,
                limit_up=[],
                limit_down=[],
            )

        up_count = sum(1 for s in stocks if s.change_pct > 0)
        down_count = sum(1 for s in stocks if s.change_pct < 0)
        flat_count = len(stocks) - up_count - down_count

        avg_change = sum(s.change_pct for s in stocks) / len(stocks)

        # 找出表现最好和最差的
        sorted_stocks = sorted(stocks, key=lambda s: s.change_pct, reverse=True)
        best = sorted_stocks[0]
        worst = sorted_stocks[-1]

        # 找出涨跌停
        limit_up = [s for s in stocks if s.change_pct >= LIMIT_UP_THRESHOLD]
        limit_down = [s for s in stocks if s.change_pct <= LIMIT_DOWN_THRESHOLD]

        return WatchlistSummary(
            total=len(stocks),
            up_count=up_count,
            down_count=down_count,
            flat_count=flat_count,
            avg_change=avg_change,
            best=best,
            worst=worst,
            limit_up=limit_up,
            limit_down=limit_down,
        )

    def format_watch(self, stocks: list[StockSpot]) -> str:
        """格式化行情输出"""
        if not stocks:
            return "自选股列表为空，请先添加股票"

        lines = [
            f"自选股行情 (共 {len(stocks)} 只)",
            "=" * 60,
            f"{'代码':<8} {'名称':<10} {'现价':>8} {'涨跌幅':>8} {'成交额(亿)':>10} {'换手率':>8}",
            "-" * 60,
        ]

        for s in stocks:
            change_str = f"+{s.change_pct:.2f}%" if s.change_pct > 0 else f"{s.change_pct:.2f}%"
            lines.append(
                f"{s.code:<8} {s.name:<10} {s.price:>8.2f} {change_str:>8} {s.amount:>10.1f} {s.turnover_rate:>7.2f}%"
            )

        # 统计
        summary = self.analyze(stocks)
        lines.append("-" * 60)
        lines.append(
            f"统计: {summary.up_count}涨 {summary.down_count}跌 {summary.flat_count}平 "
            f"平均 {summary.avg_change:+.2f}%"
        )

        return "\n".join(lines)

    def format_analyze(self, stocks: list[StockSpot]) -> str:
        """格式化分析输出"""
        if not stocks:
            return "自选股列表为空，请先添加股票"

        summary = self.analyze(stocks)

        lines = [
            "自选股分析报告",
            "=" * 40,
            "",
            "市场统计:",
            f"  总数: {summary.total}",
            f"  上涨: {summary.up_count} ({summary.up_count/summary.total*100:.0f}%)",
            f"  下跌: {summary.down_count} ({summary.down_count/summary.total*100:.0f}%)",
            f"  平均涨跌幅: {summary.avg_change:+.2f}%",
            "",
        ]

        if summary.best:
            lines.extend([
                "表现最好:",
                f"  {summary.best.name}({summary.best.code}): {summary.best.change_pct:+.2f}%",
                "",
            ])

        if summary.worst:
            lines.extend([
                "表现最差:",
                f"  {summary.worst.name}({summary.worst.code}): {summary.worst.change_pct:+.2f}%",
                "",
            ])

        if summary.limit_up:
            lines.append("涨停提醒:")
            for s in summary.limit_up:
                lines.append(f"  {s.name}({s.code}) 涨停")
            lines.append("")

        if summary.limit_down:
            lines.append("跌停提醒:")
            for s in summary.limit_down:
                lines.append(f"  {s.name}({s.code}) 跌停")
            lines.append("")

        if not summary.limit_up and not summary.limit_down:
            lines.append("异动提醒: 无")

        return "\n".join(lines)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="自选股监控")
    parser.add_argument("--add", type=str, help="添加股票，逗号分隔")
    parser.add_argument("--add-file", type=str, help="从文件添加股票")
    parser.add_argument("--remove", type=str, help="移除股票")
    parser.add_argument("--list", action="store_true", help="列出所有自选股")
    parser.add_argument("--clear", action="store_true", help="清空自选股")
    parser.add_argument("--yes", action="store_true", help="确认操作")
    parser.add_argument("--watch", action="store_true", help="获取实时行情")
    parser.add_argument("--analyze", action="store_true", help="快速分析")
    parser.add_argument("--top-n", type=int, help="限制显示数量")

    return parser.parse_args()


async def main():
    args = parse_args()
    manager = WatchlistManager()
    processor = WatchlistProcessor(manager)

    # 添加股票
    if args.add:
        codes = [c.strip() for c in args.add.split(",") if c.strip()]
        added, existing = manager.add(codes)
        if added:
            print(f"已添加: {', '.join(added)}")
        if existing:
            print(f"已存在: {', '.join(existing)}")
        return

    # 从文件添加
    if args.add_file:
        with open(args.add_file, "r", encoding="utf-8") as f:
            codes = [line.strip() for line in f if line.strip()]
        added, existing = manager.add(codes)
        print(f"已添加 {len(added)} 只股票")
        if existing:
            print(f"已存在 {len(existing)} 只股票")
        return

    # 移除股票
    if args.remove:
        codes = [c.strip() for c in args.remove.split(",") if c.strip()]
        watchlist = manager.load()
        original_len = len(watchlist.stocks)
        codes_to_remove = set(codes)
        watchlist.stocks = [
            item for item in watchlist.stocks
            if manager._normalize_code(item.code) not in {manager._normalize_code(c) for c in codes_to_remove}
        ]
        removed = original_len - len(watchlist.stocks)
        if removed > 0:
            manager.save(watchlist)
        print(f"已移除 {removed} 只股票")
        return

    # 列出股票
    if args.list:
        watchlist = manager.load()
        if not watchlist.stocks:
            print("自选股列表为空")
        else:
            print(f"自选股列表 (共 {len(watchlist.stocks)} 只):")
            for item in watchlist.stocks:
                note_str = f" - {item.note}" if item.note else ""
                print(f"  {item.code} (添加于 {item.added_at}){note_str}")
        return

    # 清空
    if args.clear:
        if not args.yes:
            confirm = input("确认清空自选股列表？(y/N): ")
            if confirm.lower() != "y":
                print("已取消")
                return
        manager.clear()
        print("已清空自选股列表")
        return

    # 获取行情
    if args.watch:
        stocks = await processor.watch(args.top_n)
        print(processor.format_watch(stocks))
        return

    # 快速分析
    if args.analyze:
        stocks = await processor.watch()
        print(processor.format_analyze(stocks))
        return

    # 无参数时显示帮助
    print("使用 --help 查看帮助")


if __name__ == "__main__":
    asyncio.run(main())
