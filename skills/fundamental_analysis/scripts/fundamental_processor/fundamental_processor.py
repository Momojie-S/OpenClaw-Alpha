# -*- coding: utf-8 -*-
"""基本面分析 Processor"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

# 导入数据源模块以注册数据源
import openclaw_alpha.data_sources

from skills.fundamental_analysis.scripts.financial_fetcher import fetch_financial
from skills.fundamental_analysis.scripts.valuation_fetcher import fetch_valuation

logger = logging.getLogger(__name__)

SKILL_NAME = "fundamental_analysis"
PROCESSOR_NAME = "fundamental_processor"


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="基本面分析")
    parser.add_argument("--code", required=True, help="股票代码（如 000001）")
    parser.add_argument(
        "--include-history",
        action="store_true",
        help="是否包含估值历史数据",
    )
    return parser.parse_args()


def _rate_valuation(pe: Optional[float], pb: Optional[float]) -> Dict:
    """估值评级

    Args:
        pe: PE (TTM)
        pb: PB

    Returns:
        估值评级字典
    """
    result = {"pe_ttm": pe, "pb": pb}

    # PE 评级
    if pe is not None:
        if pe < 15:
            result["pe_rating"] = "低估"
        elif pe <= 25:
            result["pe_rating"] = "合理"
        else:
            result["pe_rating"] = "高估"

    # PB 评级
    if pb is not None:
        if pb < 1.5:
            result["pb_rating"] = "低估"
        elif pb <= 3:
            result["pb_rating"] = "合理"
        else:
            result["pb_rating"] = "高估"

    return result


def _rate_roe(roe: Optional[float]) -> str:
    """ROE 评级

    Args:
        roe: ROE (%)

    Returns:
        评级字符串
    """
    if roe is None:
        return "未知"
    if roe > 15:
        return "优秀"
    if roe > 10:
        return "良好"
    if roe > 5:
        return "一般"
    return "较差"


def _rate_growth(
    revenue_growth: Optional[float], profit_growth: Optional[float]
) -> str:
    """成长性评级

    Args:
        revenue_growth: 营收增长 (%)
        profit_growth: 利润增长 (%)

    Returns:
        评级字符串
    """
    # 都为空，返回未知
    if revenue_growth is None and profit_growth is None:
        return "未知"

    # 判断逻辑
    if revenue_growth is not None and profit_growth is not None:
        if revenue_growth > 20 and profit_growth > 20:
            return "高增长"
        if revenue_growth > 0 and profit_growth > 0:
            return "稳定增长"
        if revenue_growth < -10 or profit_growth < -10:
            return "大幅下滑"
        return "下滑"

    # 部分数据
    if revenue_growth is not None:
        if revenue_growth > 20:
            return "高增长"
        if revenue_growth > 0:
            return "稳定增长"
        return "下滑"

    if profit_growth is not None:
        if profit_growth > 20:
            return "高增长"
        if profit_growth > 0:
            return "稳定增长"
        return "下滑"


def _rate_debt_ratio(debt_ratio: Optional[float], name: str) -> str:
    """资产负债率评级

    Args:
        debt_ratio: 资产负债率 (%)
        name: 股票名称（用于判断金融行业）

    Returns:
        评级字符串
    """
    if debt_ratio is None:
        return "未知"

    # 金融行业（银行、保险）特殊处理
    is_financial = any(k in name for k in ["银行", "保险", "证券"])

    if is_financial:
        if debt_ratio > 95:
            return "关注"
        return "正常"

    # 一般行业
    if debt_ratio < 40:
        return "健康"
    if debt_ratio <= 60:
        return "正常"
    if debt_ratio <= 70:
        return "关注"
    return "风险"


def _calc_overall_score(data: dict) -> dict:
    """计算综合评分

    评分维度：
    - 估值（权重 25%）：低估=100, 合理=70, 高估=40
    - 盈利能力（权重 30%）：优秀=100, 良好=80, 一般=50, 较差=20
    - 成长性（权重 25%）：高增长=100, 稳定增长=70, 下滑=40, 大幅下滑=10
    - 财务健康（权重 20%）：健康=100, 正常=70, 关注=40, 风险=10

    Args:
        data: 分析结果字典

    Returns:
        综合评分字典，包含 score 和 rating
    """
    weights = {
        "valuation": 0.25,
        "profitability": 0.30,
        "growth": 0.25,
        "financial_health": 0.20,
    }

    # 评级到分数的映射
    valuation_scores = {"低估": 100, "合理": 70, "高估": 40}
    profitability_scores = {"优秀": 100, "良好": 80, "一般": 50, "较差": 20, "未知": 50}
    growth_scores = {
        "高增长": 100,
        "稳定增长": 70,
        "下滑": 40,
        "大幅下滑": 10,
        "未知": 50,
    }
    health_scores = {"健康": 100, "正常": 70, "关注": 40, "风险": 10, "未知": 50}

    # 计算各维度分数
    scores = {}
    details = {}

    # 估值分数（取 PE 和 PB 的平均）
    pe_rating = data.get("valuation", {}).get("pe_rating")
    pb_rating = data.get("valuation", {}).get("pb_rating")
    val_scores = []
    if pe_rating and pe_rating in valuation_scores:
        val_scores.append(valuation_scores[pe_rating])
    if pb_rating and pb_rating in valuation_scores:
        val_scores.append(valuation_scores[pb_rating])
    if val_scores:
        scores["valuation"] = sum(val_scores) / len(val_scores)
        details["valuation"] = round(scores["valuation"], 1)
    else:
        scores["valuation"] = 50  # 默认中等分
        details["valuation"] = 50

    # 盈利能力分数
    roe_rating = data.get("profitability", {}).get("roe_rating", "未知")
    scores["profitability"] = profitability_scores.get(roe_rating, 50)
    details["profitability"] = scores["profitability"]

    # 成长性分数
    growth_rating = data.get("growth", {}).get("growth_rating", "未知")
    scores["growth"] = growth_scores.get(growth_rating, 50)
    details["growth"] = scores["growth"]

    # 财务健康分数
    debt_rating = data.get("financial_health", {}).get("debt_rating", "未知")
    scores["financial_health"] = health_scores.get(debt_rating, 50)
    details["financial_health"] = scores["financial_health"]

    # 加权计算总分
    total_score = sum(scores[k] * weights[k] for k in weights)
    total_score = round(total_score, 1)

    # 综合评级
    if total_score >= 80:
        rating = "优秀"
    elif total_score >= 65:
        rating = "良好"
    elif total_score >= 50:
        rating = "一般"
    elif total_score >= 35:
        rating = "较差"
    else:
        rating = "危险"

    return {
        "score": total_score,
        "rating": rating,
        "details": details,
    }


def _generate_summary(data: dict) -> str:
    """生成总结

    Args:
        data: 分析结果字典

    Returns:
        总结字符串
    """
    parts = []

    # 综合评分
    overall = data.get("overall", {})
    if overall:
        parts.append(f"综合评分 {overall.get('score', '-')} 分（{overall.get('rating', '-')}）")

    # 估值
    pe_rating = data.get("valuation", {}).get("pe_rating")
    pb_rating = data.get("valuation", {}).get("pb_rating")

    if pe_rating == "低估" or pb_rating == "低估":
        parts.append("估值偏低")
    elif pe_rating == "高估" or pb_rating == "高估":
        parts.append("估值偏高")
    else:
        parts.append("估值合理")

    # ROE
    roe_rating = data.get("profitability", {}).get("roe_rating")
    if roe_rating in ["优秀", "良好"]:
        parts.append(f"ROE {roe_rating}")
    elif roe_rating in ["一般", "较差"]:
        parts.append(f"ROE {roe_rating}")

    # 成长性
    growth_rating = data.get("growth", {}).get("growth_rating")
    if growth_rating in ["高增长", "稳定增长"]:
        parts.append(f"成长性{growth_rating}")
    elif growth_rating in ["下滑", "大幅下滑"]:
        parts.append(f"营收{growth_rating}")

    # 财务健康
    debt_rating = data.get("financial_health", {}).get("debt_rating")
    if debt_rating in ["风险", "关注"]:
        parts.append(f"资产负债率{debt_rating}")

    return "，".join(parts) if parts else "数据不足，无法判断"


async def analyze(code: str, include_history: bool = False) -> dict:
    """基本面分析主函数

    Args:
        code: 股票代码
        include_history: 是否包含估值历史数据

    Returns:
        分析结果字典
    """
    # 1. 获取财务指标
    financial = await fetch_financial(code)

    # 2. 获取估值数据（PE、PB 最新值）
    pe_data = await fetch_valuation(code, "pe_ttm", "近一年")
    pb_data = await fetch_valuation(code, "pb", "近一年")

    # 取最新值
    pe_latest = pe_data[-1].value if pe_data else None
    pb_latest = pb_data[-1].value if pb_data else None

    # 3. 构建分析结果
    result = {
        "code": financial.code,
        "name": financial.name,
        "report_date": financial.report_date,
        "valuation": _rate_valuation(pe_latest, pb_latest),
        "profitability": {
            "roe": financial.roe,
            "roe_rating": _rate_roe(financial.roe),
            "eps": financial.eps,
            "net_margin": financial.net_profit_margin,
            "gross_margin": financial.gross_profit_margin,
        },
        "growth": {
            "revenue_growth": financial.revenue_growth,
            "profit_growth": financial.profit_growth,
            "growth_rating": _rate_growth(
                financial.revenue_growth, financial.profit_growth
            ),
        },
        "financial_health": {
            "debt_ratio": financial.debt_ratio,
            "debt_rating": _rate_debt_ratio(financial.debt_ratio, financial.name),
            "current_ratio": financial.current_ratio,
            "quick_ratio": financial.quick_ratio,
            "cash_per_share": financial.cash_per_share,
        },
    }

    # 4. 添加历史数据（可选）
    if include_history:
        result["history"] = {
            "pe": [v.to_dict() for v in pe_data[-30:]],  # 最近 30 天
            "pb": [v.to_dict() for v in pb_data[-30:]],
        }

    # 5. 计算综合评分
    result["overall"] = _calc_overall_score(result)

    # 6. 生成总结
    result["summary"] = _generate_summary(result)

    return result


def main():
    """命令行入口"""
    args = parse_args()
    result = asyncio.run(analyze(args.code, args.include_history))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
