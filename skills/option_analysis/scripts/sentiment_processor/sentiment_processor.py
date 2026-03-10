# -*- coding: utf-8 -*-
"""期权情绪分析 Processor"""

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path

# 标的代码到名称的映射
UNDERLYING_NAMES = {
    # 上交所 ETF
    "510050": "50ETF",
    "510300": "300ETF",
    "510500": "500ETF",
    "588000": "科创50ETF",
    "588080": "科创50ETF易方达",
    # 深交所 ETF
    "159919": "300ETF深",
    "159922": "500ETF深",
    "159915": "创业板ETF",
    # 股指期权
    "IO": "沪深300股指",
    "HO": "上证50股指",
    "MO": "中证1000股指"
}


def parse_args():
    parser = argparse.ArgumentParser(description="期权情绪分析")
    parser.add_argument(
        "--underlying",
        default="510050",
        help="标的代码（默认 510050 50ETF）"
    )
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="日期（默认今天）"
    )
    parser.add_argument(
        "--output",
        help="输出文件路径（可选）"
    )
    return parser.parse_args()


def get_exchange(underlying: str) -> str:
    """根据标的代码判断交易所"""
    if underlying.startswith("5"):
        return "sse"
    elif underlying.startswith("1"):
        return "szse"
    else:
        return "cffex"


def judge_pcr_sentiment(pcr: float) -> str:
    """判断 PCR 情绪"""
    if pcr > 1.2:
        return "极度悲观"
    elif pcr > 1.0:
        return "偏悲观"
    elif pcr >= 0.8:
        return "中性"
    elif pcr >= 0.7:
        return "偏乐观"
    else:
        return "极度乐观"


def judge_iv_level(iv: float) -> str:
    """判断波动率水平"""
    if iv > 30:
        return "高波动"
    elif iv >= 15:
        return "正常"
    else:
        return "低波动"


def generate_signal(pcr_sentiment: str, iv_level: str) -> str:
    """生成综合信号"""
    signals = []

    if pcr_sentiment == "极度悲观":
        signals.append("市场过度恐慌，可能反转向上")
    elif pcr_sentiment == "极度乐观":
        signals.append("市场过度亢奋，可能反转向下")

    if iv_level == "高波动":
        signals.append("波动率高企，可能接近底部")
    elif iv_level == "低波动":
        signals.append("波动率低位，可能即将变盘")

    if not signals:
        signals.append("市场情绪平稳")

    return "；".join(signals)


async def analyze_sentiment(underlying: str, date: str) -> dict:
    """分析期权情绪"""
    from ..option_data_fetcher import fetch

    exchange = get_exchange(underlying)
    name = UNDERLYING_NAMES.get(underlying, underlying)

    # 获取每日统计数据
    if exchange == "sse":
        daily_stats = await fetch("daily_stats_sse", date=date)
    elif exchange == "szse":
        daily_stats = await fetch("daily_stats_szse", date=date)
    else:
        # 股指期权暂不支持
        return {
            "underlying": name,
            "code": underlying,
            "date": date,
            "error": "股指期权暂不支持"
        }

    # 筛选目标标的数据
    target_stats = None
    for stat in daily_stats:
        # 尝试匹配标的代码或名称
        if underlying in str(stat) or name in str(stat):
            target_stats = stat
            break

    if not target_stats and daily_stats:
        # 如果没找到，使用第一条数据（通常是主力品种）
        target_stats = daily_stats[0]

    if not target_stats:
        return {
            "underlying": name,
            "code": underlying,
            "date": date,
            "error": "未找到数据"
        }

    # 提取数据
    call_volume = target_stats.get("认购成交量", 0) or 0
    put_volume = target_stats.get("认沽成交量", 0) or 0
    call_oi = target_stats.get("未平仓认购合约数", 0) or 0
    put_oi = target_stats.get("未平仓认沽合约数", 0) or 0

    # 计算 PCR
    pcr_volume = put_volume / call_volume if call_volume > 0 else 0
    pcr_oi = put_oi / call_oi if call_oi > 0 else 0

    # 判断情绪
    pcr_sentiment = judge_pcr_sentiment(pcr_volume)
    iv_level = "正常"  # 每日统计数据不包含 IV，需要单独查询
    iv_atm = None

    # 尝试获取风险指标（仅上交所）
    if exchange == "sse":
        try:
            risk_data = await fetch("risk_indicator", underlying=underlying)
            if risk_data and risk_data.get("iv_stats"):
                iv_atm = risk_data["iv_stats"].get("atm_iv")
                if iv_atm:
                    iv_level = judge_iv_level(iv_atm * 100)  # 转为百分比
        except Exception:
            pass

    # 生成信号
    signal = generate_signal(pcr_sentiment, iv_level)

    return {
        "underlying": name,
        "code": underlying,
        "date": date,
        "call_volume": int(call_volume),
        "put_volume": int(put_volume),
        "pcr_volume": round(pcr_volume, 2),
        "call_oi": int(call_oi),
        "put_oi": int(put_oi),
        "pcr_oi": round(pcr_oi, 2),
        "sentiment": pcr_sentiment,
        "iv_atm": round(iv_atm * 100, 1) if iv_atm else None,
        "iv_level": iv_level,
        "signal": signal
    }


def get_output_path(date: str, processor_name: str) -> Path:
    """获取输出文件路径"""
    return Path(f".openclaw_alpha/option_analysis/{date}/{processor_name}.json")


def main():
    args = parse_args()

    result = asyncio.run(analyze_sentiment(args.underlying, args.date))

    # 保存到文件
    output_path = Path(args.output) if args.output else get_output_path(args.date, "sentiment")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    # 打印结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
