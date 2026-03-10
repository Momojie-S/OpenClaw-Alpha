# -*- coding: utf-8 -*-
"""个股对比分析处理器"""

import argparse
import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

from openclaw_alpha.core.processor_utils import get_output_path


@dataclass
class StockMetrics:
    """股票指标"""
    code: str
    name: str
    price: float
    change_pct: float
    turnover_rate: float
    amount: float  # 亿
    market_cap: float  # 亿
    pe: Optional[float] = None
    pb: Optional[float] = None
    net_inflow: Optional[float] = None  # 主力净流入（亿）


@dataclass
class StockScore:
    """股票评分"""
    code: str
    name: str
    total_score: float
    valuation_score: float  # 估值得分
    momentum_score: float  # 动量得分
    liquidity_score: float  # 流动性得分
    fund_score: float  # 资金得分
    rank: int = 0


@dataclass
class CompareResult:
    """对比结果"""
    date: str
    stocks: list[StockMetrics]
    scores: list[StockScore]
    winner: Optional[str] = None  # 综合最佳

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "stocks": [asdict(s) for s in self.stocks],
            "scores": [asdict(s) for s in self.scores],
            "winner": self.winner,
        }


async def fetch_stock_metrics(symbol: str, date: str) -> StockMetrics:
    """获取单只股票的指标

    Args:
        symbol: 股票代码
        date: 日期

    Returns:
        StockMetrics
    """
    from openclaw_alpha.skills.stock_analysis.stock_fetcher import fetch

    # 获取行情数据
    data = await fetch(symbol, date)

    # 检查是否有错误
    if "error" in data:
        raise ValueError(data["error"])

    return StockMetrics(
        code=symbol,
        name=data.get("name", ""),
        price=data.get("price", {}).get("close", 0),
        change_pct=data.get("price", {}).get("pct_change", 0),
        turnover_rate=data.get("volume", {}).get("turnover_rate", 0),
        amount=data.get("volume", {}).get("amount", 0) / 1e8,  # 转为亿
        market_cap=data.get("market_cap", {}).get("total", 0) / 1e8,  # 转为亿
        pe=None,  # 新接口不提供
        pb=None,  # 新接口不提供
        net_inflow=None,  # 需要单独获取
    )


async def fetch_all_metrics(symbols: list[str], date: str) -> list[StockMetrics]:
    """获取所有股票的指标

    Args:
        symbols: 股票代码列表
        date: 日期

    Returns:
        指标列表
    """
    tasks = [fetch_stock_metrics(s, date) for s in symbols]
    return await asyncio.gather(*tasks)


def calculate_scores(metrics: list[StockMetrics]) -> list[StockScore]:
    """计算评分

    评分维度：
    - 估值得分（PE、PB）：越低越好
    - 动量得分（涨跌幅）：越高越好
    - 流动性得分（换手率、成交额）：适中最好
    - 资金得分（净流入）：越高越好

    Args:
        metrics: 股票指标列表

    Returns:
        评分列表
    """
    if not metrics:
        return []

    scores = []

    # 计算各维度得分
    for m in metrics:
        # 估值得分（PE）
        valuation_score = 0
        if m.pe is not None and m.pe > 0:
            if m.pe < 15:
                valuation_score = 90
            elif m.pe < 30:
                valuation_score = 70
            elif m.pe < 50:
                valuation_score = 50
            else:
                valuation_score = 30

        # 动量得分
        momentum_score = 50 + m.change_pct * 5  # 基础 50 + 涨幅贡献
        momentum_score = max(0, min(100, momentum_score))

        # 流动性得分（换手率 3-8% 最佳）
        if 3 <= m.turnover_rate <= 8:
            liquidity_score = 80
        elif m.turnover_rate < 3:
            liquidity_score = 50
        else:
            liquidity_score = max(30, 80 - (m.turnover_rate - 8) * 5)

        # 资金得分（默认 50，需要额外数据）
        fund_score = 50

        # 综合得分（加权平均）
        total_score = (
            valuation_score * 0.25 +
            momentum_score * 0.30 +
            liquidity_score * 0.25 +
            fund_score * 0.20
        )

        scores.append(StockScore(
            code=m.code,
            name=m.name,
            total_score=round(total_score, 1),
            valuation_score=round(valuation_score, 1),
            momentum_score=round(momentum_score, 1),
            liquidity_score=round(liquidity_score, 1),
            fund_score=round(fund_score, 1),
        ))

    # 排名
    sorted_scores = sorted(scores, key=lambda x: x.total_score, reverse=True)
    for i, s in enumerate(sorted_scores):
        s.rank = i + 1

    return sorted_scores


async def compare_stocks(
    symbols: list[str],
    date: str,
) -> CompareResult:
    """对比多只股票

    Args:
        symbols: 股票代码列表
        date: 日期

    Returns:
        CompareResult
    """
    # 获取指标
    metrics = await fetch_all_metrics(symbols, date)

    # 计算评分
    scores = calculate_scores(metrics)

    # 找出综合最佳
    winner = scores[0].code if scores else None

    return CompareResult(
        date=date,
        stocks=metrics,
        scores=scores,
        winner=winner,
    )


def format_compare_result(result: CompareResult) -> str:
    """格式化对比结果

    Args:
        result: 对比结果

    Returns:
        格式化的文本
    """
    lines = [
        "=" * 70,
        f"个股对比分析 - {result.date}",
        "=" * 70,
        "",
    ]

    # 基本信息对比表
    lines.append("【基本信息对比】")
    lines.append("")
    header = f"{'代码':<8} {'名称':<10} {'现价':>8} {'涨跌%':>8} {'换手%':>8} {'市值(亿)':>10}"
    lines.append(header)
    lines.append("-" * len(header))

    for s in result.stocks:
        lines.append(
            f"{s.code:<8} {s.name:<10} {s.price:>8.2f} {s.change_pct:>8.2f} "
            f"{s.turnover_rate:>8.2f} {s.market_cap:>10.1f}"
        )

    lines.append("")

    # 评分对比表
    lines.append("【综合评分对比】")
    lines.append("")
    header = f"{'排名':>4} {'代码':<8} {'名称':<10} {'综合':>8} {'估值':>8} {'动量':>8} {'流动':>8}"
    lines.append(header)
    lines.append("-" * len(header))

    for s in result.scores:
        marker = "⭐" if s.code == result.winner else "  "
        lines.append(
            f"{marker}{s.rank:>2} {s.code:<8} {s.name:<10} {s.total_score:>8.1f} "
            f"{s.valuation_score:>8.1f} {s.momentum_score:>8.1f} {s.liquidity_score:>8.1f}"
        )

    # 综合建议
    if result.winner:
        winner_score = next(s for s in result.scores if s.code == result.winner)
        lines.extend([
            "",
            "【综合建议】",
            f"综合评分最高：{winner_score.code} {winner_score.name}（{winner_score.total_score}分）",
            "",
            "评分说明：",
            "  - 估值得分：基于 PE，越低越好（PE<15: 90分, 15-30: 70分, 30-50: 50分）",
            "  - 动量得分：基于涨跌幅，越高越好",
            "  - 流动性得分：基于换手率，3-8% 最佳",
            "  - 资金得分：基于主力资金流向（需要额外数据）",
            "",
            "⚠️ 提示：评分仅供参考，投资决策需结合更多因素",
        ])

    return "\n".join(lines)


def save_result(result: CompareResult, date: str) -> str:
    """保存对比结果

    Args:
        result: 对比结果
        date: 日期

    Returns:
        保存路径
    """
    output_path = get_output_path(
        skill_name="stock_compare",
        processor_name="compare_processor",
        date=date,
        ext="json",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description="个股对比分析")
    parser.add_argument("symbols", help="股票代码（逗号分隔）")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--output", action="store_true", help="保存结果")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",")]

    if len(symbols) < 2:
        print("请至少提供 2 只股票进行对比")
        return

    if len(symbols) > 10:
        print("最多对比 10 只股票")
        symbols = symbols[:10]

    result = asyncio.run(compare_stocks(symbols, args.date))

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(format_compare_result(result))

    if args.output:
        path = save_result(result, args.date)
        print(f"\n结果已保存: {path}")


if __name__ == "__main__":
    main()
