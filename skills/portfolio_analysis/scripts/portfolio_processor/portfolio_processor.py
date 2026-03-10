# -*- coding: utf-8 -*-
"""持仓分析 Processor"""

from dataclasses import dataclass, asdict
from typing import Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class Holding:
    """持仓"""

    code: str
    name: str
    shares: int
    price: float
    market_value: float
    weight: float
    cost: float | None = None
    profit: float | None = None
    profit_pct: float | None = None
    change_pct: float = 0.0
    industry: str = "未知"


@dataclass
class IndustryDistribution:
    """行业分布"""

    industry: str
    weight: float
    market_value: float
    count: int


@dataclass
class RiskAlert:
    """风险提示"""

    level: str  # "high", "medium", "low"
    type: str
    message: str
    detail: str


@dataclass
class PortfolioResult:
    """持仓分析结果"""

    total_value: float
    total_cost: float | None
    total_profit: float | None
    total_profit_pct: float | None
    holdings: list[Holding]
    industry_distribution: list[IndustryDistribution]
    risk_alerts: list[RiskAlert]
    hhi: float  # 集中度指数
    concentration_level: str  # "分散", "中等", "高度集中"


class PortfolioProcessor:
    """持仓分析处理器"""

    def __init__(self):
        pass

    def parse_holdings_string(self, holdings_str: str) -> list[dict[str, Any]]:
        """
        解析持仓字符串

        格式: "000001:1000:12.5,600000:500:8.2" 或 "000001:1000,600000:500"

        Args:
            holdings_str: 持仓字符串

        Returns:
            持仓列表
        """
        holdings = []
        parts = holdings_str.split(",")
        for part in parts:
            part = part.strip()
            if not part:
                continue
            items = part.split(":")
            if len(items) < 2:
                continue
            code = items[0].strip()
            try:
                shares = int(items[1].strip())
                cost = float(items[2].strip()) if len(items) > 2 else None
                holdings.append({"code": code, "shares": shares, "cost": cost})
            except ValueError:
                logger.warning(f"无效的持仓格式: {part}")
                continue
        return holdings

    def calculate_weights(
        self, holdings_data: list[dict[str, Any]], stock_data: dict[str, dict[str, Any]]
    ) -> list[Holding]:
        """
        计算各持仓权重

        Args:
            holdings_data: 持仓数据列表
            stock_data: 股票行情数据 {code: {price, name, change_pct, ...}}

        Returns:
            持仓列表（含权重）
        """
        # 计算总市值
        total_value = 0.0
        holdings = []

        for h in holdings_data:
            code = h["code"]
            shares = h["shares"]
            cost = h.get("cost")

            stock = stock_data.get(code, {})
            price = stock.get("price", 0)
            name = stock.get("name", code)
            change_pct = stock.get("change_pct", 0)

            market_value = price * shares
            total_value += market_value

            holding = Holding(
                code=code,
                name=name,
                shares=shares,
                price=price,
                market_value=market_value,
                weight=0,  # 稍后计算
                cost=cost,
                change_pct=change_pct,
                industry=stock.get("industry", "未知"),
            )
            holdings.append(holding)

        # 计算权重
        for h in holdings:
            if total_value > 0:
                h.weight = round(h.market_value / total_value * 100, 2)

            # 计算盈亏
            if h.cost is not None and h.cost > 0:
                h.profit = (h.price - h.cost) * h.shares
                h.profit_pct = round((h.price - h.cost) / h.cost * 100, 2)

        return holdings

    def calculate_industry_distribution(
        self, holdings: list[Holding]
    ) -> list[IndustryDistribution]:
        """
        计算行业分布

        Args:
            holdings: 持仓列表

        Returns:
            行业分布列表（按权重降序）
        """
        # 按行业聚合
        industry_data: dict[str, dict[str, float | int]] = {}
        for h in holdings:
            ind = h.industry
            if ind not in industry_data:
                industry_data[ind] = {"market_value": 0, "count": 0}
            industry_data[ind]["market_value"] += h.market_value
            industry_data[ind]["count"] += 1

        # 计算总市值
        total_value = sum(h.market_value for h in holdings)

        # 转换为列表
        result = []
        for industry, data in industry_data.items():
            weight = round(data["market_value"] / total_value * 100, 2) if total_value > 0 else 0
            result.append(
                IndustryDistribution(
                    industry=industry,
                    weight=weight,
                    market_value=round(data["market_value"], 2),
                    count=int(data["count"]),
                )
            )

        # 按权重降序
        result.sort(key=lambda x: x.weight, reverse=True)
        return result

    def calculate_hhi(self, holdings: list[Holding]) -> float:
        """
        计算集中度指数 (Herfindahl-Hirschman Index)

        Args:
            holdings: 持仓列表

        Returns:
            HHI 指数 (0-10000)
        """
        hhi = sum(h.weight**2 for h in holdings)
        return round(hhi, 2)

    def check_risks(
        self, holdings: list[Holding], industry_distribution: list[IndustryDistribution]
    ) -> list[RiskAlert]:
        """
        检查风险

        Args:
            holdings: 持仓列表
            industry_distribution: 行业分布

        Returns:
            风险提示列表
        """
        alerts = []

        # 单股集中风险
        for h in holdings:
            if h.weight > 30:
                alerts.append(
                    RiskAlert(
                        level="high",
                        type="单股集中",
                        message=f"单股集中度过高: {h.name}({h.code})",
                        detail=f"权重 {h.weight}% 超过 30% 阈值",
                    )
                )

        # 行业集中风险
        for ind in industry_distribution:
            if ind.weight > 50:
                alerts.append(
                    RiskAlert(
                        level="high",
                        type="行业集中",
                        message=f"行业集中度过高: {ind.industry}",
                        detail=f"权重 {ind.weight}% 超过 50% 阈值",
                    )
                )

        # 持仓数量风险
        stock_count = len(holdings)
        if stock_count < 3:
            alerts.append(
                RiskAlert(
                    level="medium",
                    type="持仓过少",
                    message="持仓过于集中",
                    detail=f"仅持有 {stock_count} 只股票，建议适当分散",
                )
            )
        elif stock_count > 20:
            alerts.append(
                RiskAlert(
                    level="low",
                    type="持仓过多",
                    message="持仓过于分散",
                    detail=f"持有 {stock_count} 只股票，可能分散精力",
                )
            )

        return alerts

    def process(
        self,
        holdings_input: list[dict[str, Any]],
        stock_data: dict[str, dict[str, Any]],
    ) -> PortfolioResult:
        """
        执行持仓分析

        Args:
            holdings_input: 持仓输入列表 [{code, shares, cost?}]
            stock_data: 股票行情数据 {code: {price, name, change_pct, industry?}}

        Returns:
            分析结果
        """
        # 计算权重
        holdings = self.calculate_weights(holdings_input, stock_data)

        # 计算总市值和盈亏
        total_value = sum(h.market_value for h in holdings)
        total_cost = None
        total_profit = None

        # 只要有任何持仓有成本价，就计算总盈亏
        holdings_with_cost = [h for h in holdings if h.cost is not None]
        if holdings_with_cost:
            total_cost = sum(h.cost * h.shares for h in holdings_with_cost)
            total_profit = sum(h.profit for h in holdings_with_cost if h.profit is not None)

        # 计算行业分布
        industry_distribution = self.calculate_industry_distribution(holdings)

        # 计算集中度
        hhi = self.calculate_hhi(holdings)
        if hhi < 1500:
            concentration_level = "分散"
        elif hhi < 2500:
            concentration_level = "中等"
        else:
            concentration_level = "高度集中"

        # 检查风险
        risk_alerts = self.check_risks(holdings, industry_distribution)

        # 计算总盈亏比例
        total_profit_pct = None
        if total_cost and total_cost > 0:
            total_profit_pct = round(total_profit / total_cost * 100, 2)

        return PortfolioResult(
            total_value=round(total_value, 2),
            total_cost=round(total_cost, 2) if total_cost else None,
            total_profit=round(total_profit, 2) if total_profit else None,
            total_profit_pct=total_profit_pct,
            holdings=holdings,
            industry_distribution=industry_distribution,
            risk_alerts=risk_alerts,
            hhi=hhi,
            concentration_level=concentration_level,
        )

    def format_summary(self, result: PortfolioResult) -> str:
        """
        格式化精简摘要

        Args:
            result: 分析结果

        Returns:
            格式化字符串
        """
        lines = []
        lines.append("持仓分析报告")
        lines.append("=" * 40)

        # 总览
        lines.append(f"总市值：¥{result.total_value:,.2f}")
        if result.total_profit is not None:
            profit_sign = "+" if result.total_profit >= 0 else ""
            lines.append(
                f"总盈亏：{profit_sign}¥{result.total_profit:,.2f} ({profit_sign}{result.total_profit_pct}%)"
            )
        lines.append(f"集中度：{result.concentration_level} (HHI: {result.hhi})")
        lines.append("")

        # 持仓分布
        lines.append("持仓分布（按市值）：")
        for i, h in enumerate(sorted(result.holdings, key=lambda x: x.market_value, reverse=True)[
            :10
        ]):
            profit_str = ""
            if h.profit is not None:
                sign = "+" if h.profit >= 0 else ""
                profit_str = f" - {sign}¥{h.profit:,.0f} ({sign}{h.profit_pct}%)"
            lines.append(
                f"{i+1}. {h.name}({h.code}) - {h.weight}% - ¥{h.market_value:,.0f}{profit_str}"
            )
        lines.append("")

        # 行业分布
        lines.append("行业分布：")
        for ind in result.industry_distribution[:5]:
            lines.append(f"- {ind.industry}: {ind.weight}% ({ind.count}只)")
        lines.append("")

        # 风险提示
        if result.risk_alerts:
            lines.append("风险提示：")
            for alert in result.risk_alerts:
                icon = {"high": "⚠️", "medium": "⚡", "low": "ℹ️"}.get(alert.level, "•")
                lines.append(f"{icon} {alert.message}: {alert.detail}")

        return "\n".join(lines)

    def to_dict(self, result: PortfolioResult) -> dict[str, Any]:
        """
        转换为字典

        Args:
            result: 分析结果

        Returns:
            字典表示
        """
        return {
            "summary": {
                "total_value": result.total_value,
                "total_cost": result.total_cost,
                "total_profit": result.total_profit,
                "total_profit_pct": result.total_profit_pct,
                "hhi": result.hhi,
                "concentration_level": result.concentration_level,
            },
            "holdings": [asdict(h) for h in result.holdings],
            "industry_distribution": [asdict(i) for i in result.industry_distribution],
            "risk_alerts": [asdict(a) for a in result.risk_alerts],
        }
