# -*- coding: utf-8 -*-
"""行业景气度 Processor"""

import argparse
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from openclaw_alpha.core.processor_utils import get_output_path, load_output
from ..sector_valuation_fetcher import fetch as fetch_valuation

SKILL_NAME = "industry_trend"
PROCESSOR_NAME = "prosperity"


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="行业景气度分析")
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="查询日期（YYYY-MM-DD），默认当日",
    )
    parser.add_argument(
        "--category",
        default="L1",
        choices=["L1", "L2", "L3"],
        help="行业层级，默认 L1（一级行业）",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="返回 TOP N 结果，默认 10",
    )
    return parser.parse_args()


async def process(date: str, category: str = "L1", top_n: int = 10) -> dict[str, Any]:
    """计算行业景气度

    Args:
        date: 查询日期（YYYY-MM-DD）
        category: 行业层级（L1/L2/L3）
        top_n: 返回 TOP N 结果

    Returns:
        景气度分析结果
    """
    # 1. 获取当前数据
    current_data = await fetch_valuation(category=category, date=date)

    if not current_data:
        return {
            "date": date,
            "category": category,
            "boards": [],
            "message": "无数据",
        }

    # 2. 获取上周数据（用于计算环比）
    prev_date = await _get_previous_week_date(date, category)
    prev_data = await fetch_valuation(category=category, date=prev_date) if prev_date else []

    # 3. 构建上周数据映射
    prev_map = {item['code']: item for item in prev_data}

    # 4. 计算景气度
    boards = []
    for item in current_data:
        code = item['code']
        prev_item = prev_map.get(code)

        # 计算估值趋势
        pe_change = _calc_change(item['pe'], prev_item['pe'] if prev_item else None)
        pb_change = _calc_change(item['pb'], prev_item['pb'] if prev_item else None)
        valuation_trend = _judge_valuation_trend(pe_change, pb_change)

        # 计算市值变化
        mv_change = _calc_change(
            item['float_mv'],
            prev_item['float_mv'] if prev_item else None
        )

        # 计算景气度评分
        score = _calc_prosperity_score(
            valuation_trend=valuation_trend,
            pct_change=item['pct_change'],
            mv_change=mv_change,
        )

        # 判断景气度等级
        level = _judge_prosperity_level(score)

        boards.append({
            'name': item['name'],
            'code': code,
            'pe': item['pe'],
            'pb': item['pb'],
            'pe_change_week': round(pe_change, 2) if pe_change is not None else None,
            'pb_change_week': round(pb_change, 2) if pb_change is not None else None,
            'valuation_trend': valuation_trend,
            'pct_change': round(item['pct_change'], 2),
            'mv_change_week': round(mv_change, 2) if mv_change is not None else None,
            'prosperity_score': round(score, 2),
            'level': level,
        })

    # 5. 按景气度评分排序
    boards.sort(key=lambda x: x['prosperity_score'], reverse=True)

    # 6. 保存完整数据
    output_path = get_output_path(SKILL_NAME, PROCESSOR_NAME, date, ext="json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'date': date,
            'category': category,
            'boards': boards,
        }, f, ensure_ascii=False, indent=2)

    # 7. 返回精简结果（TOP N）
    return {
        'date': date,
        'category': category,
        'boards': boards[:top_n],
    }


async def _get_previous_week_date(date: str, category: str) -> str | None:
    """获取上一周的交易日日期

    Args:
        date: 当前日期
        category: 行业层级

    Returns:
        上一周的日期，如果找不到则返回 None
    """
    # 解析日期
    current = datetime.strptime(date, "%Y-%m-%d")

    # 回溯最多 10 天，找到有数据的上一周
    for i in range(7, 15):
        prev = current - timedelta(days=i)
        prev_date = prev.strftime("%Y-%m-%d")

        # 尝试获取数据
        data = await fetch_valuation(category=category, date=prev_date)
        if data:
            return prev_date

    return None


def _calc_change(current: float | None, previous: float | None) -> float | None:
    """计算变化百分比

    Args:
        current: 当前值
        previous: 之前的值

    Returns:
        变化百分比，如果无法计算则返回 None
    """
    if current is None or previous is None or previous == 0:
        return None

    return (current - previous) / previous * 100


def _judge_valuation_trend(pe_change: float | None, pb_change: float | None) -> str:
    """判断估值趋势

    Args:
        pe_change: PE 周环比变化
        pb_change: PB 周环比变化

    Returns:
        趋势：上升/稳定/下降/新
    """
    # 无历史数据
    if pe_change is None and pb_change is None:
        return "新"

    # PE 趋势判断（阈值 ±5%）
    pe_trend = "稳定"
    if pe_change is not None:
        if pe_change > 5:
            pe_trend = "上升"
        elif pe_change < -5:
            pe_trend = "下降"

    # PB 趋势判断（阈值 ±3%）
    pb_trend = "稳定"
    if pb_change is not None:
        if pb_change > 3:
            pb_trend = "上升"
        elif pb_change < -3:
            pb_trend = "下降"

    # 综合判断
    if pe_trend == pb_trend:
        return pe_trend
    else:
        return "稳定"


def _calc_prosperity_score(
    valuation_trend: str,
    pct_change: float,
    mv_change: float | None,
) -> float:
    """计算景气度评分

    Args:
        valuation_trend: 估值趋势
        pct_change: 涨跌幅
        mv_change: 市值变化

    Returns:
        景气度评分（0-100）
    """
    # 1. 估值趋势分（40%）
    trend_scores = {"上升": 100, "稳定": 60, "下降": 20, "新": 60}
    trend_score = trend_scores.get(valuation_trend, 60)

    # 2. 价格趋势分（40%）- 基于涨跌幅归一化
    # 涨跌幅范围假设 -10% ~ +10%，映射到 0-100
    price_score = max(0, min(100, (pct_change + 10) * 5))

    # 3. 市值变化分（20%）- 基于市值变化归一化
    if mv_change is not None:
        # 市值变化范围假设 -10% ~ +10%，映射到 0-100
        mv_score = max(0, min(100, (mv_change + 10) * 5))
    else:
        mv_score = 50  # 无数据时取中间值

    # 加权计算总分
    score = trend_score * 0.4 + price_score * 0.4 + mv_score * 0.2

    return score


def _judge_prosperity_level(score: float) -> str:
    """判断景气度等级

    Args:
        score: 景气度评分

    Returns:
        等级：高景气/中等景气/低景气
    """
    if score >= 70:
        return "高景气"
    elif score >= 50:
        return "中等景气"
    else:
        return "低景气"


def main():
    """命令行入口"""
    args = parse_args()
    result = asyncio.run(process(args.date, args.category, args.top_n))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
