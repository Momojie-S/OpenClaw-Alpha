# -*- coding: utf-8 -*-
"""情绪周期 Processor"""

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入 limit_up_tracker 的 fetcher
from skills.limit_up_tracker.scripts.limit_up_fetcher import fetch as fetch_limit_up
from skills.limit_up_tracker.scripts.limit_up_fetcher.models import LimitUpType


@dataclass
class SentimentIndicators:
    """情绪指标"""

    # 涨停家数
    limit_up_count: int = 0
    # 炸板家数
    broken_count: int = 0
    # 炸板率 (%)
    broken_rate: float = 0.0
    # 最高连板数
    max_continuous: int = 0
    # 昨日涨停今日平均涨跌幅 (%)
    prev_avg_change: float = 0.0
    # 昨日涨停盈利比例 (%)
    prev_profit_rate: float = 0.0

    def to_dict(self) -> dict:
        return {
            "limit_up_count": self.limit_up_count,
            "broken_count": self.broken_count,
            "broken_rate": round(self.broken_rate, 2),
            "max_continuous": self.max_continuous,
            "prev_avg_change": round(self.prev_avg_change, 2),
            "prev_profit_rate": round(self.prev_profit_rate, 2),
        }


@dataclass
class SentimentCycleResult:
    """情绪周期结果"""

    # 交易日期
    date: str
    # 情绪周期
    cycle: Literal["启动", "加速", "高潮", "分歧", "退潮"]
    # 情绪指标
    indicators: SentimentIndicators
    # 判断理由
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "cycle": self.cycle,
            "indicators": self.indicators.to_dict(),
            "reasons": self.reasons,
        }


class SentimentCycleProcessor:
    """情绪周期处理器"""

    def __init__(self, date: str):
        self.date = date
        self.indicators = SentimentIndicators()

    async def analyze(self) -> SentimentCycleResult:
        """分析情绪周期"""
        # 1. 获取数据
        await self._fetch_data()

        # 2. 判断情绪周期
        cycle, reasons = self._determine_cycle()

        return SentimentCycleResult(
            date=self.date,
            cycle=cycle,
            indicators=self.indicators,
            reasons=reasons,
        )

    async def _fetch_data(self):
        """获取必要数据"""
        # 获取今日涨停
        limit_up_result = await fetch_limit_up(self.date, LimitUpType.LIMIT_UP)
        self.indicators.limit_up_count = limit_up_result.total

        # 计算最高连板数
        if limit_up_result.items:
            self.indicators.max_continuous = max(
                item.continuous for item in limit_up_result.items
            )

        # 获取炸板数据
        try:
            broken_result = await fetch_limit_up(self.date, LimitUpType.BROKEN)
            self.indicators.broken_count = broken_result.total
        except Exception:
            # 如果获取炸板数据失败，设为 0
            self.indicators.broken_count = 0

        # 计算炸板率
        total_attempted = self.indicators.limit_up_count + self.indicators.broken_count
        if total_attempted > 0:
            self.indicators.broken_rate = (
                self.indicators.broken_count / total_attempted
            ) * 100

        # 获取昨日涨停表现
        try:
            prev_result = await fetch_limit_up(self.date, LimitUpType.PREVIOUS)
            if prev_result.items:
                # 计算平均涨跌幅
                changes = [item.change_pct for item in prev_result.items]
                self.indicators.prev_avg_change = sum(changes) / len(changes)

                # 计算盈利比例
                profit_count = sum(1 for c in changes if c > 0)
                self.indicators.prev_profit_rate = (profit_count / len(changes)) * 100
        except Exception:
            # 如果获取昨日涨停数据失败，保持默认值
            pass

    def _determine_cycle(self) -> tuple[str, list[str]]:
        """判断情绪周期"""
        reasons = []
        ind = self.indicators

        # 退潮：涨停家数锐减，昨日涨停亏损率高
        if ind.limit_up_count < 30 and ind.prev_profit_rate < 40:
            reasons.append(f"涨停家数锐减（{ind.limit_up_count} 只）")
            reasons.append(f"昨日涨停亏损率高（盈利比例 {ind.prev_profit_rate:.1f}%）")
            return "退潮", reasons

        # 分歧：炸板率高，昨日涨停表现分化
        if ind.broken_rate > 50:
            reasons.append(f"炸板率高（{ind.broken_rate:.1f}%）")
            if 40 <= ind.prev_profit_rate <= 60:
                reasons.append(f"昨日涨停表现分化（盈利比例 {ind.prev_profit_rate:.1f}%）")
            return "分歧", reasons

        # 高潮：涨停家数达到峰值，炸板率开始上升
        if ind.limit_up_count > 100 and ind.max_continuous >= 5:
            reasons.append(f"涨停家数达到峰值（{ind.limit_up_count} 只）")
            reasons.append(f"最高连板数 {ind.max_continuous} 板")
            if ind.broken_rate > 30:
                reasons.append(f"炸板率开始上升（{ind.broken_rate:.1f}%）")
            return "高潮", reasons

        # 加速：涨停家数持续增加，2 板以上股增多
        if ind.limit_up_count > 50 and ind.max_continuous >= 3:
            reasons.append(f"涨停家数增加（{ind.limit_up_count} 只）")
            reasons.append(f"最高连板数 {ind.max_continuous} 板")
            return "加速", reasons

        # 启动：涨停家数增加，炸板率低，昨日涨停正收益
        if (
            ind.limit_up_count > 20
            and ind.broken_rate < 30
            and ind.prev_avg_change > 0
        ):
            reasons.append(f"涨停家数增加（{ind.limit_up_count} 只）")
            reasons.append(f"炸板率低（{ind.broken_rate:.1f}%）")
            reasons.append(f"昨日涨停正收益（平均涨跌 {ind.prev_avg_change:.2f}%）")
            return "启动", reasons

        # 默认：启动（无明确信号时）
        reasons.append("暂无明显信号，市场情绪中性")
        return "启动", reasons


def format_output(result: SentimentCycleResult) -> str:
    """格式化输出"""
    lines = [
        f"情绪周期分析 ({result.date})",
        "=" * 60,
        "",
        f"当前周期: {result.cycle}",
        "",
        "情绪指标:",
        f"  涨停家数: {result.indicators.limit_up_count}",
        f"  炸板家数: {result.indicators.broken_count}",
        f"  炸板率: {result.indicators.broken_rate:.2f}%",
        f"  最高连板: {result.indicators.max_continuous} 板",
        f"  昨日涨停平均涨跌: {result.indicators.prev_avg_change:.2f}%",
        f"  昨日涨停盈利比例: {result.indicators.prev_profit_rate:.2f}%",
        "",
        "判断理由:",
    ]

    for reason in result.reasons:
        lines.append(f"  - {reason}")

    # 添加操作建议
    lines.extend([
        "",
        "操作建议:",
    ])

    suggestions = {
        "启动": "可关注龙头，尝试建仓",
        "加速": "持仓待涨，注意风险",
        "高潮": "谨慎追高，考虑减仓",
        "分歧": "减仓观望，等待方向",
        "退潮": "及时止损，空仓等待",
    }
    lines.append(f"  {suggestions.get(result.cycle, '观望为主')}")

    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description="情绪周期分析")
    parser.add_argument(
        "--date", default=datetime.now().strftime("%Y-%m-%d"), help="交易日期"
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    # 分析情绪周期
    processor = SentimentCycleProcessor(args.date)
    result = await processor.analyze()

    # 输出格式化结果
    print(format_output(result))

    # 保存完整数据到文件
    output_dir = Path.cwd() / ".openclaw_alpha" / "theme_speculation" / args.date
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "sentiment_cycle.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

    print(f"\n完整数据已保存到: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
