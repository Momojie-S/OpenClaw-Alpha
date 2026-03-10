# -*- coding: utf-8 -*-
"""定投建议 Processor - 基于股债性价比的智能定投策略"""

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

# 导入股债性价比 processor（复用现有能力）
from skills.market_sentiment.scripts.equity_bond_ratio_processor.equity_bond_ratio_processor import (
    EquityBondRatioProcessor,
)

SKILL_NAME = "smart_dip"
PROCESSOR_NAME = "dip_advice"


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="智能定投建议")
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="分析日期，默认今天",
    )
    parser.add_argument(
        "--base-amount",
        type=float,
        default=1000,
        help="基准金额（元），默认 1000",
    )
    parser.add_argument(
        "--strategy",
        choices=["fed_model"],
        default="fed_model",
        help="策略类型：fed_model（股债性价比驱动）",
    )
    parser.add_argument("--output", choices=["text", "json"], default="text", help="输出格式")
    return parser.parse_args()


def get_multiplier(equity_bond_ratio: float) -> tuple[float, str, str]:
    """
    根据股债性价比确定定投倍数

    Args:
        equity_bond_ratio: 股债性价比（百分比）

    Returns:
        (倍数, 市场状态, 操作建议)
    """
    if equity_bond_ratio > 3.0:
        return 2.0, "极度低估", "大幅加仓"
    elif equity_bond_ratio > 2.0:
        return 1.5, "低估", "增加定投"
    elif equity_bond_ratio > 0.0:
        return 1.0, "合理", "正常定投"
    elif equity_bond_ratio > -1.0:
        return 0.5, "高估", "减半定投"
    else:
        return 0.0, "极度高估", "暂停定投"


async def get_dip_advice(date: str, base_amount: float, strategy: str) -> dict[str, Any]:
    """
    获取定投建议

    Args:
        date: 分析日期
        base_amount: 基准金额
        strategy: 策略类型

    Returns:
        定投建议结果
    """
    # 获取股债性价比数据
    processor = EquityBondRatioProcessor()
    ebr_data = await processor.process(date=date, lookback_days=252)

    # 检查是否有错误
    if "error" in ebr_data:
        raise ValueError(
            f"获取股债性价比数据失败: {ebr_data['error']}。"
            f"请检查网络连接或稍后重试"
        )

    if not ebr_data or "risk_premium" not in ebr_data:
        raise ValueError(
            "无法获取股债性价比数据。"
            f"请检查数据源是否可用，或稍后重试"
        )

    current_ratio = ebr_data["risk_premium"]
    multiplier, status, action = get_multiplier(current_ratio)
    amount = base_amount * multiplier

    # 计算历史平均倍数（基于历史分位数据推断）
    # 注意：这里简化处理，实际可以加载历史数据计算
    avg_multiplier_3m = None
    avg_multiplier_6m = None

    # 如果有历史分位数据，可以推断大致的倍数水平
    if "percentile" in ebr_data:
        percentile = ebr_data["percentile"]
        # 根据历史分位推断平均倍数（简化版）
        if percentile < 30:
            avg_multiplier_3m = 1.5
            avg_multiplier_6m = 1.3
        elif percentile < 70:
            avg_multiplier_3m = 1.0
            avg_multiplier_6m = 1.0
        else:
            avg_multiplier_3m = 0.5
            avg_multiplier_6m = 0.7

    result = {
        "date": date,
        "strategy": strategy,
        "base_amount": base_amount,
        "valuation": {
            "equity_bond_ratio": current_ratio,
            "status": status,
        },
        "recommendation": {
            "multiplier": multiplier,
            "amount": round(amount, 2),
            "action": action,
        },
        "history": {
            "avg_multiplier_3m": avg_multiplier_3m,
            "avg_multiplier_6m": avg_multiplier_6m,
        },
    }

    return result


def format_text(result: dict[str, Any]) -> str:
    """格式化文本输出"""
    lines = [
        "=== 智能定投建议 ===",
        f"日期: {result['date']}",
        f"基准金额: {result['base_amount']} 元",
        "",
        "【估值分析】",
        f"股债性价比: {result['valuation']['equity_bond_ratio']:.2f}%",
        f"市场状态: {result['valuation']['status']}",
        "",
        "【定投建议】",
        f"倍数: {result['recommendation']['multiplier']}x",
        f"建议金额: {result['recommendation']['amount']:.0f} 元",
        f"操作: {result['recommendation']['action']}",
        "",
        "【历史参考】",
    ]

    if result["history"]["avg_multiplier_3m"] is not None:
        lines.append(f"近3月平均倍数: {result['history']['avg_multiplier_3m']}x")
    else:
        lines.append("近3月平均倍数: 暂无数据")

    if result["history"]["avg_multiplier_6m"] is not None:
        lines.append(f"近6月平均倍数: {result['history']['avg_multiplier_6m']}x")
    else:
        lines.append("近6月平均倍数: 暂无数据")

    return "\n".join(lines)


def get_output_path(skill_name: str, processor_name: str, date: str, ext: str = "json") -> Path:
    """获取输出文件路径"""
    return Path(f".openclaw_alpha/{skill_name}/{date}/{processor_name}.{ext}")


async def main():
    """主入口"""
    args = parse_args()

    try:
        result = await get_dip_advice(args.date, args.base_amount, args.strategy)

        # 保存完整数据
        output_path = get_output_path(SKILL_NAME, PROCESSOR_NAME, args.date)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        # 输出结果
        if args.output == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_text(result))
            print(f"\n完整数据已保存到: {output_path}")

    except Exception as e:
        print(f"错误: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
