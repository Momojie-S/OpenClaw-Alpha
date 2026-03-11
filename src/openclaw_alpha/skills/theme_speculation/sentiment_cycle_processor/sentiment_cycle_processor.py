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

from rich.console import Console
from rich.table import Table

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入 limit_up_tracker 的 fetcher
from openclaw_alpha.skills.limit_up_tracker.limit_up_fetcher import fetch as fetch_limit_up
from openclaw_alpha.skills.limit_up_tracker.limit_up_fetcher.models import LimitUpType


@dataclass
class DataQualityScore:
    """数据质量评分"""

    # 总分（0-100）
    total: int = 0
    # 完整性评分（0-40）
    completeness: int = 0
    # 合理性评分（0-40）
    reasonableness: int = 0
    # 时效性评分（0-20）
    timeliness: int = 0
    # 等级（A/B/C/D）
    grade: str = "D"
    # 评分详情
    details: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "completeness": self.completeness,
            "reasonableness": self.reasonableness,
            "timeliness": self.timeliness,
            "grade": self.grade,
            "details": self.details,
        }


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
    # 数据异常警告
    warnings: list[str] = field(default_factory=list)
    # 数据质量评分
    quality_score: DataQualityScore = field(default_factory=DataQualityScore)

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "cycle": self.cycle,
            "indicators": self.indicators.to_dict(),
            "reasons": self.reasons,
            "warnings": self.warnings,
            "quality_score": self.quality_score.to_dict(),
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

        # 2. 检测数据异常
        warnings = self._detect_anomalies()

        # 3. 计算数据质量评分
        quality_score = self._calculate_data_quality()

        # 4. 判断情绪周期
        cycle, reasons = self._determine_cycle()

        return SentimentCycleResult(
            date=self.date,
            cycle=cycle,
            indicators=self.indicators,
            reasons=reasons,
            warnings=warnings,
            quality_score=quality_score,
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

    def _detect_anomalies(self) -> list[str]:
        """检测数据异常

        检测以下异常情况：
        1. 炸板率 = 0% 但有涨停（数据源可能缺失炸板数据）
        2. 昨日涨停盈利比例 = 0% 且平均涨跌 = 0%（数据源可能缺失昨日表现数据）
        3. 涨停数 = 0（非交易日或数据异常）

        Returns:
            警告信息列表
        """
        warnings = []
        ind = self.indicators

        # 1. 检测炸板率异常
        # 如果有涨停但炸板率为 0%，可能是数据源缺失炸板数据
        if ind.limit_up_count > 0 and ind.broken_rate == 0:
            warnings.append(
                f"数据异常：炸板率为 0%（涨停 {ind.limit_up_count} 只），"
                f"数据源可能缺失炸板数据，情绪周期判断可能不准确"
            )

        # 2. 检测昨日涨停表现异常
        # 如果盈利比例和平均涨跌都是 0%，可能是数据源缺失昨日表现数据
        if ind.prev_profit_rate == 0 and ind.prev_avg_change == 0:
            warnings.append(
                "数据异常：昨日涨停盈利比例和平均涨跌均为 0%，"
                "数据源可能缺失昨日涨停表现数据，情绪周期判断可能不准确"
            )

        # 3. 检测涨停数异常
        # 如果涨停数为 0，可能是非交易日或数据异常
        if ind.limit_up_count == 0:
            warnings.append(
                "数据异常：无涨停数据，可能是非交易日或数据源异常"
            )

        return warnings

    def _calculate_data_quality(self) -> DataQualityScore:
        """计算数据质量评分

        评分维度：
        1. 完整性（0-40分）：涨停数据、炸板数据、昨日涨停表现数据
        2. 合理性（0-40分）：炸板率、盈利比例、平均涨跌是否在合理范围
        3. 时效性（0-20分）：数据是否是最近的

        Returns:
            数据质量评分
        """
        ind = self.indicators
        details = []

        # 1. 完整性评分（0-40分）
        completeness = 0

        # 有涨停数据（10分）
        if ind.limit_up_count > 0:
            completeness += 10
            details.append("有涨停数据（+10分）")
        else:
            details.append("无涨停数据（+0分）")

        # 有炸板数据（10分）
        if ind.broken_count > 0:
            completeness += 10
            details.append("有炸板数据（+10分）")
        else:
            details.append("无炸板数据（+0分）")

        # 有昨日涨停表现数据（20分）
        if ind.prev_profit_rate > 0 or ind.prev_avg_change != 0:
            completeness += 20
            details.append("有昨日涨停表现数据（+20分）")
        else:
            details.append("无昨日涨停表现数据（+0分）")

        # 2. 合理性评分（0-40分）
        reasonableness = 0

        # 特殊情况：如果炸板率、盈利比例、平均涨跌都是 0，但涨停数 > 0
        # 说明数据源缺失部分数据，不应该认为完全合理
        if (
            ind.broken_rate == 0
            and ind.prev_profit_rate == 0
            and ind.prev_avg_change == 0
            and ind.limit_up_count > 0
        ):
            # 只给基础分（炸板率合理）
            reasonableness += 20
            details.append(f"炸板率合理（{ind.broken_rate:.1f}%，+20分）")
            details.append("盈利比例和平均涨跌均为 0%（数据可能缺失，+0分）")
        else:
            # 正常评分
            # 炸板率在合理范围 0-50%（20分）
            if 0 <= ind.broken_rate <= 50:
                reasonableness += 20
                details.append(f"炸板率合理（{ind.broken_rate:.1f}%，+20分）")
            else:
                details.append(f"炸板率异常（{ind.broken_rate:.1f}%，+0分）")

            # 昨日涨停盈利比例在合理范围 0-100%（10分）
            if 0 <= ind.prev_profit_rate <= 100:
                reasonableness += 10
                details.append(f"盈利比例合理（{ind.prev_profit_rate:.1f}%，+10分）")
            else:
                details.append(f"盈利比例异常（{ind.prev_profit_rate:.1f}%，+0分）")

            # 昨日涨停平均涨跌在合理范围 -20%~20%（10分）
            if -20 <= ind.prev_avg_change <= 20:
                reasonableness += 10
                details.append(f"平均涨跌合理（{ind.prev_avg_change:.2f}%，+10分）")
            else:
                details.append(f"平均涨跌异常（{ind.prev_avg_change:.2f}%，+0分）")

        # 3. 时效性评分（0-20分）
        timeliness = 0
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        if self.date == today or self.date == yesterday:
            timeliness += 20
            details.append(f"数据是最近的（{self.date}，+20分）")
        else:
            details.append(f"数据是历史数据（{self.date}，+0分）")

        # 计算总分
        total = completeness + reasonableness + timeliness

        # 确定等级
        if total >= 90:
            grade = "A"
        elif total >= 70:
            grade = "B"
        elif total >= 50:
            grade = "C"
        else:
            grade = "D"

        return DataQualityScore(
            total=total,
            completeness=completeness,
            reasonableness=reasonableness,
            timeliness=timeliness,
            grade=grade,
            details=details,
        )

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
        # 增加条件：昨日涨停盈利比例 > 40%（排除市场分化情况）
        if (
            ind.limit_up_count > 100
            and ind.max_continuous >= 5
            and ind.prev_profit_rate > 40
        ):
            reasons.append(f"涨停家数达到峰值（{ind.limit_up_count} 只）")
            reasons.append(f"最高连板数 {ind.max_continuous} 板")
            if ind.broken_rate > 30:
                reasons.append(f"炸板率开始上升（{ind.broken_rate:.1f}%）")
            return "高潮", reasons

        # 分歧（涨停数多但昨日表现差）：涨停数 > 50，但昨日涨停盈利比例 < 40%
        if ind.limit_up_count > 50 and ind.prev_profit_rate < 40:
            reasons.append(f"涨停家数较多（{ind.limit_up_count} 只）")
            reasons.append(f"但昨日涨停表现分化（盈利比例 {ind.prev_profit_rate:.1f}%）")
            return "分歧", reasons

        # 分歧（盈利比例高但整体亏损）：涨停数 > 50，盈利比例 > 40%，但平均涨跌 < 0
        if (
            ind.limit_up_count > 50
            and ind.prev_profit_rate > 40
            and ind.prev_avg_change < 0
        ):
            reasons.append(f"涨停家数较多（{ind.limit_up_count} 只）")
            reasons.append(f"但昨日涨停整体亏损（平均涨跌 {ind.prev_avg_change:.2f}%）")
            return "分歧", reasons

        # 加速：涨停家数持续增加，2 板以上股增多
        # 增加条件：昨日涨停盈利比例 > 40%（排除市场分化情况）
        # 增加条件：昨日涨停平均涨跌 > 0（排除整体亏损情况）
        if (
            ind.limit_up_count > 50
            and ind.max_continuous >= 3
            and ind.prev_profit_rate > 40
            and ind.prev_avg_change > 0
        ):
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
    ]

    # 如果有警告，显示警告信息
    if result.warnings:
        lines.extend([
            "",
            "⚠️  数据异常警告:",
        ])
        for warning in result.warnings:
            lines.append(f"  - {warning}")

    # 显示数据质量评分
    quality = result.quality_score
    lines.extend([
        "",
        f"📊 数据质量评分: {quality.total} 分（{quality.grade} 级）",
        f"  - 完整性: {quality.completeness} 分",
        f"  - 合理性: {quality.reasonableness} 分",
        f"  - 时效性: {quality.timeliness} 分",
    ])

    lines.extend([
        "",
        "判断理由:",
    ])

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


async def fetch_historical_data(end_date: str, days: int) -> list[SentimentCycleResult]:
    """批量获取历史情绪周期数据

    Args:
        end_date: 结束日期
        days: 回溯天数

    Returns:
        情绪周期结果列表（按日期升序）
    """
    results = []
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # 从结束日期往前推算
    for i in range(days):
        date_dt = end_dt - timedelta(days=i)
        date_str = date_dt.strftime("%Y-%m-%d")

        try:
            processor = SentimentCycleProcessor(date_str)
            result = await processor.analyze()
            results.append(result)
        except Exception as e:
            # 跳过异常数据（如周末、假期）
            print(f"跳过 {date_str}: {e}", file=sys.stderr)
            continue

    # 按日期升序排列
    results.reverse()
    return results


def format_trend_output(results: list[SentimentCycleResult]) -> str:
    """格式化趋势输出

    Args:
        results: 情绪周期结果列表

    Returns:
        格式化的输出字符串
    """
    if not results:
        return "无数据"

    # 使用 StringIO 捕获 rich 输出
    from io import StringIO
    string_io = StringIO()
    console = Console(file=string_io, force_terminal=True)

    # 创建表格
    table = Table(title="情绪周期趋势分析")
    table.add_column("日期", style="cyan")
    table.add_column("周期", style="magenta")
    table.add_column("涨停数", justify="right", style="green")
    table.add_column("炸板率", justify="right", style="yellow")
    table.add_column("最高连板", justify="right", style="red")
    table.add_column("昨日表现", justify="right", style="blue")

    # 添加数据行
    for result in results:
        ind = result.indicators
        table.add_row(
            result.date,
            result.cycle,
            str(ind.limit_up_count),
            f"{ind.broken_rate:.1f}%",
            f"{ind.max_continuous}板",
            f"{ind.prev_avg_change:+.2f}%",
        )

    # 输出表格
    console.print(table)

    # 获取表格输出
    table_output = string_io.getvalue()

    # 生成 ASCII 趋势图
    lines = [
        "",
        "涨停数趋势:",
        _generate_ascii_chart([r.indicators.limit_up_count for r in results], 20),
        "",
        "炸板率趋势 (%):",
        _generate_ascii_chart([r.indicators.broken_rate for r in results], 20),
        "",
    ]

    # 添加数据异常警告（如果有）
    warnings_dates = [r.date for r in results if r.warnings]
    if warnings_dates:
        lines.extend([
            "⚠️  数据异常日期:",
        ])
        for date in warnings_dates:
            lines.append(f"  - {date}")

    # 添加周期统计
    cycle_counts = {}
    for r in results:
        cycle_counts[r.cycle] = cycle_counts.get(r.cycle, 0) + 1

    lines.extend([
        "",
        "周期统计:",
    ])
    for cycle, count in sorted(cycle_counts.items(), key=lambda x: -x[1]):
        lines.append(f"  - {cycle}: {count} 天")

    return table_output + "\n".join(lines)


def _generate_ascii_chart(values: list[float], width: int = 20) -> str:
    """生成 ASCII 趋势图

    Args:
        values: 数值列表
        width: 图表宽度（字符数）

    Returns:
        ASCII 图表字符串
    """
    if not values or all(v == 0 for v in values):
        return "无数据"

    # 归一化到 0-1 范围
    min_val = min(values)
    max_val = max(values)

    if max_val == min_val:
        # 所有值相同
        normalized = [0.5] * len(values)
    else:
        normalized = [(v - min_val) / (max_val - min_val) for v in values]

    # 生成图表
    lines = []
    bar_chars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

    # 分成多行显示（每行显示一部分数据）
    chunk_size = width
    for i in range(0, len(normalized), chunk_size):
        chunk = normalized[i:i + chunk_size]
        row = "".join(bar_chars[int(v * 7)] for v in chunk)
        lines.append(row)

    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description="情绪周期分析")
    parser.add_argument(
        "--date", default=datetime.now().strftime("%Y-%m-%d"), help="交易日期"
    )
    parser.add_argument(
        "--days", type=int, default=1, help="回溯天数（用于趋势分析）"
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    if args.days > 1:
        # 趋势分析模式
        results = await fetch_historical_data(args.date, args.days)

        # 输出趋势表格和图表
        print(format_trend_output(results))

        # 保存完整数据到文件
        output_dir = Path.cwd() / ".openclaw_alpha" / "theme_speculation" / args.date
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "sentiment_cycle_trend.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                [r.to_dict() for r in results],
                f,
                ensure_ascii=False,
                indent=2
            )

        print(f"\n完整数据已保存到: {output_file}")
    else:
        # 单日分析模式（保持向后兼容）
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
