# -*- coding: utf-8 -*-
"""炒作风险提示 Processor"""

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
from skills.limit_up_tracker.scripts.limit_up_fetcher.models import LimitUpType


@dataclass
class RiskAlert:
    """风险提示"""

    # 风险类型
    risk_type: Literal["情绪过热", "炸板风险", "监管风险", "涨幅偏离"]
    # 风险等级
    level: Literal["高", "中", "低"]
    # 触发条件
    trigger: str
    # 风险说明
    description: str

    def to_dict(self) -> dict:
        return {
            "risk_type": self.risk_type,
            "level": self.level,
            "trigger": self.trigger,
            "description": self.description,
        }


@dataclass
class SpeculationRiskResult:
    """炒作风险结果"""

    # 股票代码
    code: str
    # 股票名称
    name: str
    # 交易日期
    date: str
    # 连板数
    continuous: int
    # 涨跌幅 (%)
    change_pct: float
    # 风险提示列表
    alerts: list[RiskAlert] = field(default_factory=list)
    # 综合风险等级
    overall_risk: Literal["高", "中", "低"] = "低"

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "date": self.date,
            "continuous": self.continuous,
            "change_pct": self.change_pct,
            "alerts": [a.to_dict() for a in self.alerts],
            "overall_risk": self.overall_risk,
        }


class SpeculationRiskProcessor:
    """炒作风险处理器"""

    def __init__(self, code: str, date: str):
        self.code = code
        self.date = date

    async def analyze(self) -> SpeculationRiskResult:
        """分析炒作风险"""
        # 1. 获取涨停数据
        limit_up_data = await self._fetch_limit_up()

        # 2. 查找目标股票
        target_stock = self._find_target_stock(limit_up_data)

        if not target_stock:
            # 如果不在涨停列表中，返回基本信息
            return SpeculationRiskResult(
                code=self.code,
                name="未知",
                date=self.date,
                continuous=0,
                change_pct=0,
                alerts=[
                    RiskAlert(
                        risk_type="涨幅偏离",
                        level="低",
                        trigger="未涨停",
                        description="该股票今日未涨停，炒作风险较低",
                    )
                ],
                overall_risk="低",
            )

        # 3. 获取市场情绪数据
        sentiment_data = await self._fetch_sentiment()

        # 4. 获取基本面数据
        fundamental_data = await self._fetch_fundamental()

        # 5. 评估风险
        result = self._evaluate_risk(
            target_stock, sentiment_data, fundamental_data
        )

        return result

    async def _fetch_limit_up(self):
        """获取涨停数据"""
        result = await fetch_limit_up(self.date, LimitUpType.LIMIT_UP)
        return result.items

    def _find_target_stock(self, items):
        """查找目标股票"""
        for item in items:
            if item.code == self.code:
                return item
        return None

    async def _fetch_sentiment(self) -> dict:
        """获取市场情绪数据"""
        try:
            # 获取涨停数据统计
            limit_up_result = await fetch_limit_up(self.date, LimitUpType.LIMIT_UP)

            # 获取炸板数据
            broken_result = await fetch_limit_up(self.date, LimitUpType.BROKEN)

            # 计算炸板率
            total = limit_up_result.total + broken_result.total
            broken_rate = (broken_result.total / total * 100) if total > 0 else 0

            # 计算最高连板数
            max_continuous = 0
            if limit_up_result.items:
                max_continuous = max(item.continuous for item in limit_up_result.items)

            return {
                "limit_up_count": limit_up_result.total,
                "broken_rate": broken_rate,
                "max_continuous": max_continuous,
            }
        except Exception:
            return {
                "limit_up_count": 0,
                "broken_rate": 0,
                "max_continuous": 0,
            }

    async def _fetch_fundamental(self) -> dict | None:
        """获取基本面数据"""
        # 暂时不获取基本面数据
        return None

    def _evaluate_risk(
        self,
        stock,
        sentiment: dict,
        fundamental: dict | None,
    ) -> SpeculationRiskResult:
        """评估炒作风险"""
        alerts = []

        # 1. 情绪过热风险
        if sentiment["limit_up_count"] > 100 and stock.continuous >= 5:
            alerts.append(
                RiskAlert(
                    risk_type="情绪过热",
                    level="高",
                    trigger=f"涨停家数{sentiment['limit_up_count']}，连板{stock.continuous}板",
                    description="市场情绪过热，短期调整风险较大",
                )
            )
        elif sentiment["limit_up_count"] > 50 and stock.continuous >= 3:
            alerts.append(
                RiskAlert(
                    risk_type="情绪过热",
                    level="中",
                    trigger=f"涨停家数{sentiment['limit_up_count']}，连板{stock.continuous}板",
                    description="市场情绪较热，注意风险",
                )
            )

        # 2. 炸板风险
        if sentiment["broken_rate"] > 50:
            alerts.append(
                RiskAlert(
                    risk_type="炸板风险",
                    level="高",
                    trigger=f"市场炸板率{sentiment['broken_rate']:.1f}%",
                    description="市场炸板率高，封板不稳",
                )
            )
        elif sentiment["broken_rate"] > 30:
            alerts.append(
                RiskAlert(
                    risk_type="炸板风险",
                    level="中",
                    trigger=f"市场炸板率{sentiment['broken_rate']:.1f}%",
                    description="市场炸板率上升，注意风险",
                )
            )

        # 3. 监管风险
        if stock.continuous >= 3:
            alerts.append(
                RiskAlert(
                    risk_type="监管风险",
                    level="高" if stock.continuous >= 5 else "中",
                    trigger=f"连续{stock.continuous}日涨停",
                    description="连续涨停可能引发监管关注",
                )
            )

        # 4. 涨幅偏离基本面
        if fundamental:
            pe = fundamental.get("pe_ttm", 0)
            industry_pe = fundamental.get("industry_pe", 0)

            if pe > 0 and industry_pe > 0:
                deviation = ((pe - industry_pe) / industry_pe) * 100

                if deviation > 100:
                    alerts.append(
                        RiskAlert(
                            risk_type="涨幅偏离",
                            level="高",
                            trigger=f"PE {pe:.1f} 偏离行业均值 {deviation:.1f}%",
                            description="估值严重偏离行业均值，基本面支撑不足",
                        )
                    )
                elif deviation > 50:
                    alerts.append(
                        RiskAlert(
                            risk_type="涨幅偏离",
                            level="中",
                            trigger=f"PE {pe:.1f} 偏离行业均值 {deviation:.1f}%",
                            description="估值偏离行业均值，注意风险",
                        )
                    )

        # 计算综合风险等级
        overall_risk = self._calculate_overall_risk(alerts)

        return SpeculationRiskResult(
            code=stock.code,
            name=stock.name,
            date=self.date,
            continuous=stock.continuous,
            change_pct=stock.change_pct,
            alerts=alerts,
            overall_risk=overall_risk,
        )

    def _calculate_overall_risk(self, alerts: list[RiskAlert]) -> Literal["高", "中", "低"]:
        """计算综合风险等级"""
        if not alerts:
            return "低"

        high_count = sum(1 for a in alerts if a.level == "高")
        medium_count = sum(1 for a in alerts if a.level == "中")

        if high_count >= 2 or (high_count >= 1 and medium_count >= 2):
            return "高"
        elif high_count >= 1 or medium_count >= 2:
            return "中"
        else:
            return "低"


def format_output(result: SpeculationRiskResult) -> str:
    """格式化输出"""
    lines = [
        f"炒作风险提示 ({result.date})",
        "=" * 70,
        "",
        f"股票: {result.code} {result.name}",
        f"连板: {result.continuous} 板",
        f"涨跌幅: {result.change_pct:.2f}%",
        "",
        f"综合风险等级: {result.overall_risk}",
        "",
    ]

    if result.alerts:
        lines.append("风险提示:")
        for alert in result.alerts:
            lines.extend([
                f"  [{alert.level}] {alert.risk_type}",
                f"    触发条件: {alert.trigger}",
                f"    说明: {alert.description}",
                "",
            ])
    else:
        lines.append("暂无明显风险提示")

    # 添加操作建议
    lines.extend([
        "",
        "操作建议:",
    ])

    if result.overall_risk == "高":
        lines.append("  风险较高，建议减仓或观望")
    elif result.overall_risk == "中":
        lines.append("  风险中等，谨慎持仓，注意止损")
    else:
        lines.append("  风险较低，可继续观察")

    return "\n".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description="炒作风险提示")
    parser.add_argument("--symbol", required=True, help="股票代码")
    parser.add_argument(
        "--date", default=datetime.now().strftime("%Y-%m-%d"), help="交易日期"
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    # 分析风险
    processor = SpeculationRiskProcessor(args.symbol, args.date)
    result = await processor.analyze()

    # 输出格式化结果
    print(format_output(result))

    # 保存完整数据到文件
    output_dir = Path.cwd() / ".openclaw_alpha" / "theme_speculation" / args.date
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"risk_{args.symbol}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

    print(f"\n完整数据已保存到: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
