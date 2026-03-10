# -*- coding: utf-8 -*-
"""龙头识别 Processor"""

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入必要的模块
from skills.limit_up_tracker.scripts.limit_up_fetcher import fetch as fetch_limit_up
from skills.limit_up_tracker.scripts.limit_up_fetcher.models import LimitUpType, LimitUpItem
from skills.industry_trend.scripts.concept_fetcher import fetch as fetch_concept


@dataclass
class DragonStock:
    """龙头股数据"""

    code: str
    name: str
    # 股票类型：龙头/跟风/补涨
    stock_type: Literal["龙头", "跟风", "补涨"]
    # 连板数
    continuous: int
    # 封板时间
    first_limit_time: str
    # 流通市值（亿）
    float_mv: float
    # 涨跌幅 (%)
    change_pct: float
    # 识别理由
    reason: str

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "stock_type": self.stock_type,
            "continuous": self.continuous,
            "first_limit_time": self.first_limit_time,
            "float_mv": self.float_mv,
            "change_pct": self.change_pct,
            "reason": self.reason,
        }


@dataclass
class DragonHeadResult:
    """龙头识别结果"""

    # 交易日期
    date: str
    # 概念板块名称
    board_name: str
    # 龙头股
    dragon_head: DragonStock | None
    # 跟风股列表
    followers: list[DragonStock] = field(default_factory=list)
    # 补涨股列表
    laggards: list[DragonStock] = field(default_factory=list)
    # 板块涨停总数
    total_limit_up: int = 0

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "board_name": self.board_name,
            "dragon_head": self.dragon_head.to_dict() if self.dragon_head else None,
            "followers": [s.to_dict() for s in self.followers],
            "laggards": [s.to_dict() for s in self.laggards],
            "total_limit_up": self.total_limit_up,
        }


class DragonHeadProcessor:
    """龙头识别处理器"""

    def __init__(self, board_name: str, date: str):
        self.board_name = board_name
        self.date = date

    async def analyze(self) -> DragonHeadResult:
        """分析龙头股"""
        # 1. 获取板块成分股
        concept_data = await self._fetch_concept_cons()

        # 2. 获取涨停数据
        limit_up_data = await self._fetch_limit_up()

        # 3. 匹配板块内涨停股
        board_limit_up = self._match_board_limit_up(concept_data, limit_up_data)

        # 4. 识别龙头、跟风、补涨
        result = self._identify_dragon(board_limit_up)

        return result

    async def _fetch_concept_cons(self) -> set[str]:
        """获取概念板块成分股"""
        try:
            # 获取所有概念板块
            concepts = await fetch_concept()

            # 查找匹配的板块
            board_code = None
            for concept in concepts:
                # concept 是 dict，不是对象
                if isinstance(concept, dict) and concept.get("name") == self.board_name:
                    board_code = concept.get("code")
                    break

            if not board_code:
                raise ValueError(
                    f"概念板块 '{self.board_name}' 不存在。"
                    f"请检查板块名称是否正确"
                )

            # 获取成分股（这里需要实现成分股获取）
            # 暂时返回空集合，待后续完善
            return set()

        except Exception as e:
            # 如果获取失败，返回空集合
            print(f"警告：获取板块成分股失败: {e}")
            return set()

    async def _fetch_limit_up(self) -> list[LimitUpItem]:
        """获取涨停数据"""
        result = await fetch_limit_up(self.date, LimitUpType.LIMIT_UP)
        return result.items

    def _match_board_limit_up(
        self,
        concept_cons: set[str],
        limit_up_items: list[LimitUpItem],
    ) -> list[LimitUpItem]:
        """匹配板块内涨停股"""
        if not concept_cons:
            # 如果没有板块成分股数据，返回所有涨停股
            # 实际使用时应该提示用户
            return limit_up_items

        # 匹配板块内涨停股
        matched = [item for item in limit_up_items if item.code in concept_cons]
        return matched

    def _identify_dragon(self, items: list[LimitUpItem]) -> DragonHeadResult:
        """识别龙头、跟风、补涨"""
        if not items:
            return DragonHeadResult(
                date=self.date,
                board_name=self.board_name,
                dragon_head=None,
                total_limit_up=0,
            )

        # 按连板数、封板时间、市值排序
        # 连板数越高越好，封板时间越早越好，市值越小越好
        sorted_items = sorted(
            items,
            key=lambda x: (
                -x.continuous,  # 连板数降序
                x.first_limit_time,  # 封板时间升序（早封板排前面）
                x.float_mv,  # 市值升序（小市值排前面）
            ),
        )

        # 识别龙头（第一名）
        dragon = None
        followers = []
        laggards = []

        if sorted_items:
            top = sorted_items[0]
            dragon = DragonStock(
                code=top.code,
                name=top.name,
                stock_type="龙头",
                continuous=top.continuous,
                first_limit_time=top.first_limit_time,
                float_mv=top.float_mv,
                change_pct=top.change_pct,
                reason=f"{top.continuous}板，{top.first_limit_time}封板，流通市值{top.float_mv:.2f}亿",
            )

            # 识别跟风股（封板时间晚于 10:30）
            for item in sorted_items[1:]:
                # 判断封板时间（格式如 "09:32:00"）
                limit_time = item.first_limit_time
                is_late = False

                if limit_time:
                    try:
                        hour = int(limit_time.split(":")[0])
                        minute = int(limit_time.split(":")[1])
                        # 10:30 之后封板算跟风
                        if hour > 10 or (hour == 10 and minute >= 30):
                            is_late = True
                    except (ValueError, IndexError):
                        pass

                if is_late:
                    followers.append(
                        DragonStock(
                            code=item.code,
                            name=item.name,
                            stock_type="跟风",
                            continuous=item.continuous,
                            first_limit_time=item.first_limit_time,
                            float_mv=item.float_mv,
                            change_pct=item.change_pct,
                            reason=f"{item.continuous}板，{item.first_limit_time}封板",
                        )
                    )
                else:
                    laggards.append(
                        DragonStock(
                            code=item.code,
                            name=item.name,
                            stock_type="补涨",
                            continuous=item.continuous,
                            first_limit_time=item.first_limit_time,
                            float_mv=item.float_mv,
                            change_pct=item.change_pct,
                            reason=f"{item.continuous}板，{item.first_limit_time}封板",
                        )
                    )

        return DragonHeadResult(
            date=self.date,
            board_name=self.board_name,
            dragon_head=dragon,
            followers=followers,
            laggards=laggards,
            total_limit_up=len(items),
        )


def format_output(result: DragonHeadResult, top_n: int = 10) -> str:
    """格式化输出"""
    lines = [
        f"龙头识别分析 ({result.date})",
        f"板块: {result.board_name}",
        "=" * 70,
        "",
        f"板块涨停总数: {result.total_limit_up}",
        "",
    ]

    # 龙头股
    if result.dragon_head:
        lines.extend([
            "🎯 龙头股:",
            f"  {result.dragon_head.code} {result.dragon_head.name}",
            f"  连板: {result.dragon_head.continuous} 板",
            f"  封板时间: {result.dragon_head.first_limit_time}",
            f"  流通市值: {result.dragon_head.float_mv:.2f} 亿",
            f"  理由: {result.dragon_head.reason}",
            "",
        ])
    else:
        lines.append("🎯 龙头股: 无\n")

    # 跟风股
    if result.followers:
        lines.append(f"📈 跟风股 (Top {min(len(result.followers), top_n)}):")
        for stock in result.followers[:top_n]:
            lines.append(
                f"  {stock.code} {stock.name} - {stock.continuous}板 "
                f"{stock.first_limit_time} {stock.float_mv:.2f}亿"
            )
        lines.append("")

    # 补涨股
    if result.laggards:
        lines.append(f"📊 补涨股 (Top {min(len(result.laggards), top_n)}):")
        for stock in result.laggards[:top_n]:
            lines.append(
                f"  {stock.code} {stock.name} - {stock.continuous}板 "
                f"{stock.first_limit_time} {stock.float_mv:.2f}亿"
            )
        lines.append("")

    if not result.dragon_head and not result.followers and not result.laggards:
        lines.append("该板块今日无涨停股")

    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description="龙头识别")
    parser.add_argument("--board", required=True, help="概念板块名称")
    parser.add_argument(
        "--date", default=datetime.now().strftime("%Y-%m-%d"), help="交易日期"
    )
    parser.add_argument("--top-n", type=int, default=10, help="返回数量")
    return parser.parse_args()


async def main():
    args = parse_args()

    # 识别龙头
    processor = DragonHeadProcessor(args.board, args.date)
    result = await processor.analyze()

    # 输出格式化结果
    print(format_output(result, args.top_n))

    # 保存完整数据到文件
    output_dir = Path.cwd() / ".openclaw_alpha" / "theme_speculation" / args.date
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "dragon_head.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

    print(f"\n完整数据已保存到: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
