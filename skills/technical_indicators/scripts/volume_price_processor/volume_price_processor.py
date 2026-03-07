# -*- coding: utf-8 -*-
"""量价关系分析 Processor

分析成交量与价格的关系，判断趋势的可靠性和可能的转折点。
"""

import argparse
import asyncio
import json
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from openclaw_alpha.core.processor_utils import get_output_path

# 使用绝对导入
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from skills.technical_indicators.scripts.history_fetcher import fetch as fetch_history


class VolumePriceProcessor:
    """量价关系分析处理器"""

    def __init__(self, symbol: str, days: int = 60):
        """初始化

        Args:
            symbol: 股票代码
            days: 历史天数
        """
        self.symbol = symbol
        self.days = days
        self.df = None

    async def analyze(self) -> dict[str, Any]:
        """分析量价关系

        Returns:
            分析结果字典
        """
        # 获取历史数据
        self.df = await fetch_history(self.symbol, days=self.days)

        if self.df.empty:
            return {
                "symbol": self.symbol,
                "error": "无法获取历史数据",
                "date": datetime.now().strftime("%Y-%m-%d"),
            }

        # 计算各项指标
        obv_result = self._calculate_obv()
        correlation_result = self._calculate_correlation()
        ma_volume_result = self._calculate_ma_volume()
        volume_ratio_result = self._calculate_volume_ratio()

        # 综合判断量价关系
        relationship = self._analyze_relationship(
            obv_result, correlation_result, ma_volume_result, volume_ratio_result
        )

        # 构建结果
        result = {
            "symbol": self.symbol,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "data_range": {
                "start": self.df.iloc[0]["date"],
                "end": self.df.iloc[-1]["date"],
                "days": len(self.df),
            },
            "indicators": {
                "obv": obv_result,
                "correlation": correlation_result,
                "ma_volume": ma_volume_result,
                "volume_ratio": volume_ratio_result,
            },
            "relationship": relationship,
        }

        return result

    def _calculate_obv(self) -> dict:
        """计算 OBV（能量潮）指标

        OBV 通过累计成交量变化来判断资金流向。

        Returns:
            {"value": float, "trend": str, "trend_days": int}
        """
        import talib

        close = self.df["close"].values
        volume = self.df["volume"].values

        obv = talib.OBV(close, volume)

        # 获取最新值
        current_obv = float(obv[-1]) if not np.isnan(obv[-1]) else 0.0

        # 判断 OBV 趋势（最近 5 天）
        recent_obv = obv[-5:]
        if len(recent_obv) >= 2 and not np.any(np.isnan(recent_obv)):
            if recent_obv[-1] > recent_obv[0]:
                trend = "上升"
                # 计算连续上升天数
                trend_days = 0
                for i in range(len(obv) - 1, 0, -1):
                    if obv[i] > obv[i - 1]:
                        trend_days += 1
                    else:
                        break
            elif recent_obv[-1] < recent_obv[0]:
                trend = "下降"
                # 计算连续下降天数
                trend_days = 0
                for i in range(len(obv) - 1, 0, -1):
                    if obv[i] < obv[i - 1]:
                        trend_days += 1
                    else:
                        break
            else:
                trend = "平稳"
                trend_days = 0
        else:
            trend = "未知"
            trend_days = 0

        return {
            "value": current_obv,
            "trend": trend,
            "trend_days": trend_days,
            "series": obv[-10:].tolist(),
        }

    def _calculate_correlation(self) -> dict:
        """计算价格与成交量的相关系数

        Returns:
            {"value": float, "period": int, "interpretation": str}
        """
        close = self.df["close"].values
        volume = self.df["volume"].values

        # 计算最近 20 天的相关系数
        period = min(20, len(close))
        recent_close = close[-period:]
        recent_volume = volume[-period:]

        # 计算变化率
        close_change = np.diff(recent_close) / recent_close[:-1]
        volume_change = np.diff(recent_volume) / recent_volume[:-1]

        # 过滤无效值
        valid_mask = ~(np.isnan(close_change) | np.isnan(volume_change) | np.isinf(volume_change))
        close_change = close_change[valid_mask]
        volume_change = volume_change[valid_mask]

        if len(close_change) < 5:
            return {
                "value": 0.0,
                "period": period,
                "interpretation": "数据不足",
            }

        correlation = np.corrcoef(close_change, volume_change)[0, 1]

        if np.isnan(correlation):
            correlation = 0.0

        # 解释相关系数
        if correlation > 0.5:
            interpretation = "强正相关（量价齐升）"
        elif correlation > 0.2:
            interpretation = "弱正相关（量价同向）"
        elif correlation > -0.2:
            interpretation = "无明显关联"
        elif correlation > -0.5:
            interpretation = "弱负相关（量价背离）"
        else:
            interpretation = "强负相关（严重背离）"

        return {
            "value": float(correlation),
            "period": period,
            "interpretation": interpretation,
        }

    def _calculate_ma_volume(self) -> dict:
        """计算成交量均线

        Returns:
            {"ma5": float, "ma10": float, "ma20": float, "status": str}
        """
        volume = self.df["volume"]

        ma5 = volume.rolling(window=5).mean().iloc[-1]
        ma10 = volume.rolling(window=10).mean().iloc[-1]
        ma20 = volume.rolling(window=20).mean().iloc[-1]
        current_volume = volume.iloc[-1]

        # 判断成交量状态
        if current_volume > ma5 > ma10 > ma20:
            status = "放量"
        elif current_volume < ma5 < ma10 < ma20:
            status = "缩量"
        elif current_volume > ma5 * 2:
            status = "巨量"
        elif current_volume < ma5 * 0.5:
            status = "地量"
        else:
            status = "平稳"

        return {
            "current": float(current_volume),
            "ma5": float(ma5) if not np.isnan(ma5) else 0.0,
            "ma10": float(ma10) if not np.isnan(ma10) else 0.0,
            "ma20": float(ma20) if not np.isnan(ma20) else 0.0,
            "status": status,
        }

    def _calculate_volume_ratio(self) -> dict:
        """计算量比（今日成交量 / 过去 5 日平均成交量）

        Returns:
            {"value": float, "interpretation": str}
        """
        volume = self.df["volume"].values

        if len(volume) < 6:
            return {
                "value": 1.0,
                "interpretation": "数据不足",
            }

        current_volume = volume[-1]
        avg_volume = np.mean(volume[-6:-1])  # 前 5 天平均

        if avg_volume == 0:
            ratio = 1.0
        else:
            ratio = current_volume / avg_volume

        # 解释量比
        if ratio > 3.0:
            interpretation = "异常放量（可能有大资金进出）"
        elif ratio > 2.0:
            interpretation = "明显放量（市场活跃）"
        elif ratio > 1.5:
            interpretation = "温和放量"
        elif ratio > 0.7:
            interpretation = "正常"
        elif ratio > 0.5:
            interpretation = "明显缩量"
        else:
            interpretation = "严重缩量（市场冷清）"

        return {
            "value": float(ratio),
            "interpretation": interpretation,
        }

    def _analyze_relationship(
        self,
        obv_result: dict,
        correlation_result: dict,
        ma_volume_result: dict,
        volume_ratio_result: dict,
    ) -> dict:
        """综合判断量价关系

        Args:
            obv_result: OBV 分析结果
            correlation_result: 相关系数分析结果
            ma_volume_result: 成交量均线分析结果
            volume_ratio_result: 量比分析结果

        Returns:
            {"pattern": str, "signal": str, "score": int, "description": str}
        """
        # 获取价格变化
        close = self.df["close"].values
        price_change = (close[-1] - close[-5]) / close[-5] * 100 if len(close) >= 5 else 0

        # 获取成交量变化
        volume = self.df["volume"].values
        volume_change = (volume[-1] - np.mean(volume[-5:-1])) / np.mean(volume[-5:-1]) * 100 if len(volume) >= 5 else 0

        # 判断量价关系模式
        patterns = []
        signals = []

        # 1. 基于 OBV 判断
        obv_trend = obv_result["trend"]
        if obv_trend == "上升" and price_change > 0:
            patterns.append("OBV上升+价涨")
            signals.append(1)
        elif obv_trend == "下降" and price_change < 0:
            patterns.append("OBV下降+价跌")
            signals.append(-1)
        elif obv_trend == "上升" and price_change < 0:
            patterns.append("OBV上升+价跌（背离）")
            signals.append(1)  # 可能是底部
        elif obv_trend == "下降" and price_change > 0:
            patterns.append("OBV下降+价涨（背离）")
            signals.append(-1)  # 可能是顶部

        # 2. 基于相关系数判断
        correlation = correlation_result["value"]
        if correlation > 0.3:
            patterns.append("量价正关联")
            signals.append(1)
        elif correlation < -0.3:
            patterns.append("量价背离")
            signals.append(-1)

        # 3. 基于成交量状态判断
        vol_status = ma_volume_result["status"]
        if vol_status == "放量" and price_change > 0:
            patterns.append("放量上涨")
            signals.append(1)
        elif vol_status == "缩量" and price_change > 0:
            patterns.append("缩量上涨（动力不足）")
            signals.append(-1)
        elif vol_status == "放量" and price_change < 0:
            patterns.append("放量下跌（恐慌抛售）")
            signals.append(-2)
        elif vol_status == "缩量" and price_change < 0:
            patterns.append("缩量下跌（抛压减轻）")
            signals.append(0)
        elif vol_status == "巨量":
            patterns.append("巨量异动")
            signals.append(0)

        # 4. 基于量比判断
        ratio = volume_ratio_result["value"]
        if ratio > 2.0 and price_change > 0:
            patterns.append("倍量上涨")
            signals.append(1)
        elif ratio > 2.0 and price_change < 0:
            patterns.append("倍量下跌")
            signals.append(-1)

        # 综合评分
        total_score = sum(signals)

        # 确定主要信号
        if total_score >= 2:
            main_signal = "看涨"
            description = "量价配合良好，趋势健康，可继续持有或逢低买入"
        elif total_score >= 1:
            main_signal = "偏多"
            description = "量价关系正常，趋势较稳定"
        elif total_score <= -2:
            main_signal = "看跌"
            description = "量价关系不佳，趋势可能反转或加速下跌，建议谨慎"
        elif total_score <= -1:
            main_signal = "偏空"
            description = "量价关系偏弱，需关注风险"
        else:
            main_signal = "中性"
            description = "量价关系不明确，建议观望"

        return {
            "pattern": " | ".join(patterns),
            "signal": main_signal,
            "score": total_score,
            "description": description,
            "price_change_5d": round(price_change, 2),
            "volume_change_5d": round(volume_change, 2),
        }

    def print_result(self, result: dict):
        """打印精简结果

        Args:
            result: 分析结果
        """
        print(f"\n量价关系分析 - {result['symbol']}")
        print("=" * 60)
        print(f"分析日期: {result['date']}")
        print(f"数据范围: {result['data_range']['start']} ~ {result['data_range']['end']} ({result['data_range']['days']}天)\n")

        # OBV 指标
        obv = result["indicators"]["obv"]
        print("【OBV 能量潮】")
        print(f"  当前值: {obv['value']:.0f}")
        print(f"  趋势: {obv['trend']} (连续 {obv['trend_days']} 天)")

        # 相关系数
        corr = result["indicators"]["correlation"]
        print("\n【量价相关系数】")
        print(f"  {corr['value']:.3f} - {corr['interpretation']}")

        # 成交量均线
        ma_vol = result["indicators"]["ma_volume"]
        print("\n【成交量状态】")
        print(f"  当前: {ma_vol['current']:.0f}")
        print(f"  MA5: {ma_vol['ma5']:.0f} | MA10: {ma_vol['ma10']:.0f} | MA20: {ma_vol['ma20']:.0f}")
        print(f"  状态: {ma_vol['status']}")

        # 量比
        ratio = result["indicators"]["volume_ratio"]
        print("\n【量比】")
        print(f"  {ratio['value']:.2f} - {ratio['interpretation']}")

        # 综合判断
        rel = result["relationship"]
        print("\n【量价关系判断】")
        print(f"  模式: {rel['pattern']}")
        print(f"  5日涨跌: {rel['price_change_5d']:+.2f}%")
        print(f"  5日成交量变化: {rel['volume_change_5d']:+.2f}%")
        print(f"\n  信号: {rel['signal']} (评分: {rel['score']})")
        print(f"  分析: {rel['description']}\n")


async def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="量价关系分析")
    parser.add_argument("symbol", help="股票代码")
    parser.add_argument("--days", type=int, default=60, help="历史天数（默认 60）")

    args = parser.parse_args()

    # 分析
    processor = VolumePriceProcessor(args.symbol, args.days)
    result = await processor.analyze()

    # 打印精简结果
    processor.print_result(result)

    # 保存完整结果到文件
    output_path = get_output_path(
        "technical_indicators", "volume_price_analysis", result["date"], ext="json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"完整结果已保存到: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
