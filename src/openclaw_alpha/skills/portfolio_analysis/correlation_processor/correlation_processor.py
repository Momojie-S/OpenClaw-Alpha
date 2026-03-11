# -*- coding: utf-8 -*-
"""持仓相关性分析 Processor

计算持仓股票的相关系数矩阵，评估分散化程度。
"""

import asyncio
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from ..correlation_fetcher import fetch as fetch_prices

logger = logging.getLogger(__name__)


@dataclass
class CorrelationPair:
    """股票相关性对"""

    stock1: str
    stock2: str
    correlation: float
    level: str  # "高相关", "中等相关", "低相关"


@dataclass
class CorrelationResult:
    """相关性分析结果"""

    stocks: list[str]
    correlation_matrix: list[list[float]]  # 二维数组
    high_correlation_pairs: list[CorrelationPair]
    avg_correlation: float
    diversification_score: float
    diversification_level: str  # "高度分散", "适度分散", "集中度偏高"
    suggestion: str
    analysis_date: str
    data_days: int
    failed_stocks: list[str] = field(default_factory=list)


class CorrelationProcessor:
    """持仓相关性分析处理器"""

    # 相关性阈值
    HIGH_CORRELATION_THRESHOLD = 0.7
    MEDIUM_CORRELATION_THRESHOLD = 0.4

    # 分散化评分阈值
    HIGHLY_DIVERSIFIED_THRESHOLD = 0.3  # 平均相关性 < 0.3
    MODERATELY_DIVERSIFIED_THRESHOLD = 0.5  # 平均相关性 < 0.5

    def __init__(self):
        pass

    async def analyze(
        self,
        codes: list[str],
        days: int = 60,
    ) -> CorrelationResult:
        """
        分析持仓相关性

        Args:
            codes: 股票代码列表
            days: 历史天数（默认 60 天）

        Returns:
            相关性分析结果
        """
        logger.info(f"开始分析 {len(codes)} 只股票的相关性")

        # 1. 获取历史价格数据
        price_data = await self._fetch_prices(codes, days)

        if not price_data:
            raise ValueError(
                "无法获取任何股票的价格数据。"
                f"请检查股票代码列表是否正确（共 {len(codes)} 只），或检查网络连接"
            )

        # 2. 计算收益率
        returns = self._calculate_returns(price_data)

        # 3. 计算相关系数矩阵
        corr_matrix = returns.corr()

        # 4. 分析结果
        result = self._analyze_correlation(corr_matrix, days)

        return result

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
        """
        计算收益率

        Args:
            price_data: {股票代码: DataFrame}，DataFrame 包含 date, close

        Returns:
            DataFrame，每列是一个股票的日收益率
        """
        returns_dict = {}

        for code, df in price_data.items():
            if df.empty or len(df) < 2:
                logger.warning(f"{code} 数据不足，无法计算收益率")
                continue

            # 计算日收益率
            df = df.copy()
            df["return"] = df["close"].pct_change()
            returns_dict[code] = df["return"]

        if not returns_dict:
            raise ValueError(
                "无法计算任何股票的收益率。"
                f"请检查股票是否有足够的历史数据（至少需要 2 天），"
                f"或检查股票代码是否正确"
            )

        # 合并成 DataFrame
        returns = pd.DataFrame(returns_dict)

        # 删除包含 NaN 的行
        returns = returns.dropna()

        logger.info(f"收益率数据：{len(returns)} 天，{len(returns.columns)} 只股票")

        return returns

    def _analyze_correlation(
        self,
        corr_matrix: pd.DataFrame,
        days: int,
    ) -> CorrelationResult:
        """
        分析相关系数矩阵

        Args:
            corr_matrix: 相关系数矩阵
            days: 数据天数

        Returns:
            相关性分析结果
        """
        stocks = list(corr_matrix.columns)

        # 转换为二维数组
        matrix_array = corr_matrix.values.tolist()

        # 找出高相关股票对
        high_pairs = self._find_high_correlation_pairs(corr_matrix)

        # 计算平均相关性（排除对角线）
        avg_corr = self._calculate_avg_correlation(corr_matrix)

        # 计算分散化评分
        div_score, div_level = self._calculate_diversification_score(avg_corr)

        # 生成建议
        suggestion = self._generate_suggestion(high_pairs, div_level, len(stocks))

        return CorrelationResult(
            stocks=stocks,
            correlation_matrix=matrix_array,
            high_correlation_pairs=high_pairs,
            avg_correlation=round(avg_corr, 4),
            diversification_score=round(div_score, 4),
            diversification_level=div_level,
            suggestion=suggestion,
            analysis_date=datetime.now().strftime("%Y-%m-%d"),
            data_days=days,
        )

    def _find_high_correlation_pairs(
        self,
        corr_matrix: pd.DataFrame,
    ) -> list[CorrelationPair]:
        """找出高相关股票对"""
        pairs = []
        stocks = list(corr_matrix.columns)
        n = len(stocks)

        for i in range(n):
            for j in range(i + 1, n):
                corr = corr_matrix.iloc[i, j]

                if abs(corr) >= self.HIGH_CORRELATION_THRESHOLD:
                    level = "高相关"
                elif abs(corr) >= self.MEDIUM_CORRELATION_THRESHOLD:
                    level = "中等相关"
                else:
                    continue  # 跳过低相关

                pairs.append(
                    CorrelationPair(
                        stock1=stocks[i],
                        stock2=stocks[j],
                        correlation=round(corr, 4),
                        level=level,
                    )
                )

        # 按相关性绝对值排序
        pairs.sort(key=lambda p: abs(p.correlation), reverse=True)

        return pairs

    def _calculate_avg_correlation(self, corr_matrix: pd.DataFrame) -> float:
        """计算平均相关性（排除对角线）"""
        n = len(corr_matrix)
        if n < 2:
            return 0.0

        # 提取上三角（不含对角线）
        values = []
        for i in range(n):
            for j in range(i + 1, n):
                values.append(abs(corr_matrix.iloc[i, j]))

        return np.mean(values) if values else 0.0

    def _calculate_diversification_score(
        self,
        avg_corr: float,
    ) -> tuple[float, str]:
        """
        计算分散化评分

        Args:
            avg_corr: 平均相关性

        Returns:
            (分散化评分, 分散化等级)
        """
        # 分散化评分：1 - 平均相关性（越高越好）
        score = 1 - avg_corr

        # 判断等级
        if avg_corr < self.HIGHLY_DIVERSIFIED_THRESHOLD:
            level = "高度分散"
        elif avg_corr < self.MODERATELY_DIVERSIFIED_THRESHOLD:
            level = "适度分散"
        else:
            level = "集中度偏高"

        return score, level

    def _generate_suggestion(
        self,
        high_pairs: list[CorrelationPair],
        div_level: str,
        stock_count: int,
    ) -> str:
        """生成投资建议"""
        suggestions = []

        if high_pairs:
            high_count = len([p for p in high_pairs if p.level == "高相关"])
            if high_count > 0:
                suggestions.append(f"发现 {high_count} 对高相关股票")

        if div_level == "集中度偏高":
            suggestions.append("持仓集中度较高，建议增加行业或风格多样性")
        elif div_level == "适度分散":
            suggestions.append("持仓分散度适中")
        else:
            suggestions.append("持仓高度分散，风险较低")

        if stock_count < 3:
            suggestions.append("股票数量较少，建议适当增加持仓数量")
        elif stock_count > 15:
            suggestions.append("股票数量较多，注意管理成本")

        return "；".join(suggestions)


async def process(
    codes: list[str],
    days: int = 60,
    output_format: str = "text",
) -> str | dict[str, Any]:
    """
    分析持仓相关性（便捷函数）

    Args:
        codes: 股票代码列表
        days: 历史天数
        output_format: 输出格式（"text" 或 "json"）

    Returns:
        分析结果（文本或 JSON）
    """
    processor = CorrelationProcessor()
    result = await processor.analyze(codes, days)

    if output_format == "json":
        return asdict(result)
    else:
        return _format_text(result)


def _format_text(result: CorrelationResult) -> str:
    """格式化为文本输出"""
    lines = [
        "持仓相关性分析报告",
        "=" * 50,
        f"分析日期: {result.analysis_date}",
        f"数据范围: 最近 {result.data_days} 个交易日",
        f"股票数量: {len(result.stocks)}",
        f"分析标的: {', '.join(result.stocks)}",
        "",
        "【分散化评估】",
        f"  平均相关性: {result.avg_correlation:.2%}",
        f"  分散化评分: {result.diversification_score:.2%}",
        f"  分散程度: {result.diversification_level}",
        "",
        "【高相关股票对】",
    ]

    if result.high_correlation_pairs:
        for pair in result.high_correlation_pairs[:10]:  # 只显示前 10 个
            lines.append(
                f"  {pair.stock1} ↔ {pair.stock2}: {pair.correlation:.2%} ({pair.level})"
            )
        if len(result.high_correlation_pairs) > 10:
            lines.append(f"  ... 共 {len(result.high_correlation_pairs)} 对")
    else:
        lines.append("  无高相关股票对")

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


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="持仓相关性分析")
    parser.add_argument("codes", help="股票代码列表，逗号分隔（如 000001,600000）")
    parser.add_argument("--days", type=int, default=60, help="历史天数（默认 60）")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")

    args = parser.parse_args()
    codes = args.codes.split(",")
    output_format = "json" if args.json else "text"

    async def run():
        result = await process(codes, args.days, output_format)
        print(result)

    asyncio.run(run())


if __name__ == "__main__":
    main()
