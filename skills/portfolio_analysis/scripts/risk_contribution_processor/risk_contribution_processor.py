# -*- coding: utf-8 -*-
"""风险贡献分解 Processor

计算各股票对组合风险的贡献占比，提供风险平价建议。
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from ..correlation_fetcher import fetch as fetch_prices

logger = logging.getLogger(__name__)


@dataclass
class RiskContribution:
    """单只股票的风险贡献"""

    stock: str
    weight: float  # 当前权重
    risk_contribution: float  # 风险贡献占比
    risk_contribution_pct: float  # 风险贡献百分比
    suggested_weight: float  # 风险平价建议权重
    weight_change: float  # 建议权重变化


@dataclass
class RiskContributionResult:
    """风险贡献分析结果"""

    stocks: list[RiskContribution]
    portfolio_volatility: float  # 组合波动率
    risk_concentration: float  # 风险集中度（Top 3 风险贡献占比）
    concentration_level: str  # "高度分散", "适度分散", "风险集中"
    suggestion: str
    analysis_date: str
    data_days: int
    failed_stocks: list[str] = field(default_factory=list)


class RiskContributionProcessor:
    """风险贡献分解处理器"""

    # 风险集中度阈值
    HIGH_CONCENTRATION_THRESHOLD = 0.7
    MODERATE_CONCENTRATION_THRESHOLD = 0.5

    def __init__(self):
        pass

    async def analyze(
        self,
        holdings: dict[str, float],
        days: int = 60,
    ) -> RiskContributionResult:
        """
        分析风险贡献

        Args:
            holdings: 持仓字典 {股票代码: 权重}，权重之和应为 1
            days: 历史天数（默认 60 天）

        Returns:
            风险贡献分析结果
        """
        logger.info(f"开始分析 {len(holdings)} 只股票的风险贡献")

        # 1. 验证权重
        weights = self._validate_weights(holdings)

        # 2. 获取历史价格数据
        codes = list(holdings.keys())
        price_data = await self._fetch_prices(codes, days)

        if not price_data:
            raise ValueError("无法获取任何股票的价格数据")

        # 3. 计算收益率
        returns = self._calculate_returns(price_data)

        # 4. 计算协方差矩阵
        cov_matrix = returns.cov()

        # 5. 计算风险贡献
        result = self._calculate_risk_contribution(
            codes, weights, cov_matrix, days
        )

        return result

    def _validate_weights(self, holdings: dict[str, float]) -> np.ndarray:
        """验证并归一化权重"""
        weights = np.array(list(holdings.values()))

        if np.any(weights < 0):
            raise ValueError("权重不能为负数")

        total = weights.sum()
        if total == 0:
            raise ValueError("权重之和不能为 0")

        # 归一化
        weights = weights / total

        return weights

    async def _fetch_prices(
        self,
        codes: list[str],
        days: int,
    ) -> dict[str, pd.DataFrame]:
        """获取股票历史价格"""
        try:
            data = await fetch_prices(codes, days=days, adjust="qfq")
            return data
        except Exception as e:
            logger.error(f"获取价格数据失败: {e}")
            return {}

    def _calculate_returns(
        self,
        price_data: dict[str, pd.DataFrame],
    ) -> pd.DataFrame:
        """计算收益率"""
        returns_dict = {}

        for code, df in price_data.items():
            if df.empty or len(df) < 2:
                logger.warning(f"{code} 数据不足，无法计算收益率")
                continue

            df = df.copy()
            df["return"] = df["close"].pct_change()
            returns_dict[code] = df["return"]

        if not returns_dict:
            raise ValueError("无法计算任何股票的收益率")

        returns = pd.DataFrame(returns_dict)
        returns = returns.dropna()

        logger.info(f"收益率数据：{len(returns)} 天，{len(returns.columns)} 只股票")

        return returns

    def _calculate_risk_contribution(
        self,
        codes: list[str],
        weights: np.ndarray,
        cov_matrix: pd.DataFrame,
        days: int,
    ) -> RiskContributionResult:
        """
        计算风险贡献

        风险贡献公式：
        RC_i = w_i * (Σw)_i / σ_p
        其中：
        - w_i = 资产 i 权重
        - Σ = 协方差矩阵
        - σ_p = 组合标准差
        - (Σw)_i = 协方差矩阵第 i 行与权重向量的乘积

        Args:
            codes: 股票代码列表
            weights: 权重数组
            cov_matrix: 协方差矩阵
            days: 数据天数

        Returns:
            风险贡献分析结果
        """
        # 转换为 numpy 数组
        cov = cov_matrix.values

        # 计算组合方差和标准差
        portfolio_variance = weights @ cov @ weights
        portfolio_volatility = np.sqrt(portfolio_variance)

        # 计算边际风险贡献 (Σw)
        marginal_risk = cov @ weights

        # 计算各股票的风险贡献
        risk_contributions = weights * marginal_risk / portfolio_volatility

        # 归一化为百分比
        risk_contributions_pct = risk_contributions / risk_contributions.sum()

        # 计算风险平价权重
        risk_parity_weights = self._calculate_risk_parity_weights(cov)

        # 构建结果
        stocks_result = []
        for i, code in enumerate(codes):
            stocks_result.append(
                RiskContribution(
                    stock=code,
                    weight=round(weights[i], 4),
                    risk_contribution=round(risk_contributions[i], 6),
                    risk_contribution_pct=round(risk_contributions_pct[i], 4),
                    suggested_weight=round(risk_parity_weights[i], 4),
                    weight_change=round(risk_parity_weights[i] - weights[i], 4),
                )
            )

        # 按风险贡献排序
        stocks_result.sort(key=lambda x: x.risk_contribution_pct, reverse=True)

        # 计算风险集中度
        risk_conc, conc_level = self._calculate_risk_concentration(
            risk_contributions_pct
        )

        # 生成建议
        suggestion = self._generate_suggestion(stocks_result, conc_level)

        return RiskContributionResult(
            stocks=stocks_result,
            portfolio_volatility=round(portfolio_volatility, 6),
            risk_concentration=round(risk_conc, 4),
            concentration_level=conc_level,
            suggestion=suggestion,
            analysis_date=datetime.now().strftime("%Y-%m-%d"),
            data_days=days,
        )

    def _calculate_risk_parity_weights(self, cov: np.ndarray) -> np.ndarray:
        """
        计算风险平价权重

        简化算法：权重与波动率成反比

        Args:
            cov: 协方差矩阵

        Returns:
            风险平价权重数组
        """
        # 计算各资产的波动率
        volatilities = np.sqrt(np.diag(cov))

        # 避免除以 0
        volatilities = np.maximum(volatilities, 1e-10)

        # 权重与波动率成反比
        inv_vol = 1 / volatilities
        weights = inv_vol / inv_vol.sum()

        return weights

    def _calculate_risk_concentration(
        self,
        risk_contributions_pct: np.ndarray,
    ) -> tuple[float, str]:
        """
        计算风险集中度

        Args:
            risk_contributions_pct: 风险贡献百分比数组

        Returns:
            (风险集中度, 集中度等级)
        """
        # Top 3 风险贡献占比
        sorted_risk = np.sort(risk_contributions_pct)[::-1]
        top3_conc = sorted_risk[:3].sum() if len(sorted_risk) >= 3 else sorted_risk.sum()

        # 判断等级
        if top3_conc >= self.HIGH_CONCENTRATION_THRESHOLD:
            level = "风险集中"
        elif top3_conc >= self.MODERATE_CONCENTRATION_THRESHOLD:
            level = "适度分散"
        else:
            level = "高度分散"

        return top3_conc, level

    def _generate_suggestion(
        self,
        stocks: list[RiskContribution],
        conc_level: str,
    ) -> str:
        """生成投资建议"""
        suggestions = []

        if conc_level == "风险集中":
            # 找出风险贡献最大的股票
            top_stock = stocks[0]
            suggestions.append(
                f"风险高度集中于 {top_stock.stock}（{top_stock.risk_contribution_pct:.1%}）"
            )
            if top_stock.weight_change < -0.05:
                suggestions.append(f"建议降低 {top_stock.stock} 仓位")
        elif conc_level == "适度分散":
            suggestions.append("风险分散度适中")
        else:
            suggestions.append("风险高度分散")

        # 检查是否需要调整权重
        adjustments = []
        for stock in stocks:
            if abs(stock.weight_change) > 0.1:
                direction = "增加" if stock.weight_change > 0 else "降低"
                adjustments.append(f"{direction} {stock.stock} 仓位")

        if adjustments:
            suggestions.append("，".join(adjustments[:3]))

        return "；".join(suggestions)


async def process(
    holdings: dict[str, float],
    days: int = 60,
    output_format: str = "text",
) -> str | dict[str, Any]:
    """
    分析风险贡献（便捷函数）

    Args:
        holdings: 持仓字典 {股票代码: 权重}
        days: 历史天数
        output_format: 输出格式（"text" 或 "json"）

    Returns:
        分析结果（文本或 JSON）
    """
    processor = RiskContributionProcessor()
    result = await processor.analyze(holdings, days)

    if output_format == "json":
        return asdict(result)
    else:
        return _format_text(result)


def _format_text(result: RiskContributionResult) -> str:
    """格式化为文本输出"""
    lines = [
        "风险贡献分析报告",
        "=" * 50,
        f"分析日期: {result.analysis_date}",
        f"数据范围: 最近 {result.data_days} 个交易日",
        f"组合波动率: {result.portfolio_volatility:.4%}",
        "",
        "【风险集中度】",
        f"  Top 3 风险贡献: {result.risk_concentration:.1%}",
        f"  集中度等级: {result.concentration_level}",
        "",
        "【风险贡献详情】",
    ]

    for stock in result.stocks:
        change_symbol = "↑" if stock.weight_change > 0 else "↓" if stock.weight_change < 0 else "→"
        lines.append(
            f"  {stock.stock}: "
            f"权重 {stock.weight:.1%} → "
            f"风险贡献 {stock.risk_contribution_pct:.1%} | "
            f"建议权重 {stock.suggested_weight:.1%} ({change_symbol} {abs(stock.weight_change):.1%})"
        )

    lines.extend(
        [
            "",
            "【投资建议】",
            f"  {result.suggestion}",
        ]
    )

    if result.failed_stocks:
        lines.extend(
            [
                "",
                "【数据获取失败】",
                f"  {', '.join(result.failed_stocks)}",
            ]
        )

    return "\n".join(lines)


# 命令行入口
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="风险贡献分解")
    parser.add_argument(
        "holdings",
        help="持仓信息，格式：代码:权重（如 000001:0.3,600000:0.2）",
    )
    parser.add_argument("--days", type=int, default=60, help="历史天数（默认 60）")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")

    args = parser.parse_args()

    # 解析持仓
    holdings = {}
    for item in args.holdings.split(","):
        code, weight = item.split(":")
        holdings[code.strip()] = float(weight.strip())

    async def main():
        output_format = "json" if args.json else "text"
        result = await process(holdings, args.days, output_format)
        print(result)

    asyncio.run(main())
