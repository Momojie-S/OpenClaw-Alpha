# -*- coding: utf-8 -*-
"""技术指标分析 Processor"""

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

# 默认指标参数
DEFAULT_PARAMS = {
    "macd": {"fast": 12, "slow": 26, "signal": 9},
    "rsi": {"period": 14},
    "kdj": {"n": 9, "m1": 3, "m2": 3},
    "boll": {"period": 20, "std": 2},
    "ma": {"periods": [5, 10, 20, 60]},
}


class IndicatorProcessor:
    """技术指标分析处理器"""

    def __init__(self, symbol: str, days: int = 60):
        """初始化

        Args:
            symbol: 股票代码
            days: 历史天数
        """
        self.symbol = symbol
        self.days = days
        self.df = None

    async def analyze(
        self, indicators: list[str] = None, params: dict = None
    ) -> dict[str, Any]:
        """分析技术指标

        Args:
            indicators: 指标列表（默认全部）
            params: 指标参数（可选）

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

        # 默认分析所有指标
        if not indicators:
            indicators = ["macd", "rsi", "kdj", "boll", "ma"]

        # 合并参数
        if not params:
            params = DEFAULT_PARAMS
        else:
            merged = DEFAULT_PARAMS.copy()
            merged.update(params)
            params = merged

        # 计算各指标
        indicator_values = {}
        signals = []

        if "macd" in indicators:
            macd_result = self._calculate_macd(params["macd"])
            indicator_values["macd"] = macd_result
            signal, score = self._judge_macd_signal(macd_result)
            signals.append(
                {
                    "indicator": "macd",
                    "signal": signal,
                    "score": score,
                    "description": f"DIF={macd_result['dif']:.2f}, DEA={macd_result['dea']:.2f}, MACD={macd_result['macd']:.2f}",
                }
            )

        if "rsi" in indicators:
            rsi_result = self._calculate_rsi(params["rsi"])
            indicator_values["rsi"] = rsi_result
            signal, score = self._judge_rsi_signal(rsi_result)
            signals.append(
                {
                    "indicator": "rsi",
                    "signal": signal,
                    "score": score,
                    "description": f"RSI({params['rsi']['period']})={rsi_result['value']:.2f}",
                }
            )

        if "kdj" in indicators:
            kdj_result = self._calculate_kdj(params["kdj"])
            indicator_values["kdj"] = kdj_result
            signal, score = self._judge_kdj_signal(kdj_result)
            signals.append(
                {
                    "indicator": "kdj",
                    "signal": signal,
                    "score": score,
                    "description": f"K={kdj_result['k']:.2f}, D={kdj_result['d']:.2f}, J={kdj_result['j']:.2f}",
                }
            )

        if "boll" in indicators:
            boll_result = self._calculate_boll(params["boll"])
            indicator_values["boll"] = boll_result
            signal, score = self._judge_boll_signal(boll_result)
            signals.append(
                {
                    "indicator": "boll",
                    "signal": signal,
                    "score": score,
                    "description": f"上轨={boll_result['upper']:.2f}, 中轨={boll_result['middle']:.2f}, 下轨={boll_result['lower']:.2f}",
                }
            )

        if "ma" in indicators:
            ma_result = self._calculate_ma(params["ma"])
            indicator_values["ma"] = ma_result
            signal, score = self._judge_ma_signal(ma_result)
            signals.append(
                {
                    "indicator": "ma",
                    "signal": signal,
                    "score": score,
                    "description": ", ".join(
                        [f"MA{p}={v:.2f}" for p, v in zip(params["ma"]["periods"], ma_result["values"])]
                    ),
                }
            )

        # 综合评分
        summary = self._calculate_summary(signals)

        # 构建结果
        result = {
            "symbol": self.symbol,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "data_range": {
                "start": self.df.iloc[0]["date"],
                "end": self.df.iloc[-1]["date"],
                "days": len(self.df),
            },
            "indicators": indicator_values,
            "signals": signals,
            "summary": summary,
        }

        return result

    def _calculate_macd(self, params: dict) -> dict:
        """计算 MACD 指标

        Args:
            params: {"fast": 12, "slow": 26, "signal": 9}

        Returns:
            {"dif": float, "dea": float, "macd": float, "histogram": list}
        """
        import talib

        close = self.df["close"].values
        dif, dea, macd = talib.MACD(
            close,
            fastperiod=params["fast"],
            slowperiod=params["slow"],
            signalperiod=params["signal"],
        )

        # 获取最新值
        return {
            "dif": float(dif[-1]) if not np.isnan(dif[-1]) else 0.0,
            "dea": float(dea[-1]) if not np.isnan(dea[-1]) else 0.0,
            "macd": float(macd[-1]) if not np.isnan(macd[-1]) else 0.0,
            "histogram": macd[-10:].tolist(),  # 最近 10 天的柱状图
        }

    def _calculate_rsi(self, params: dict) -> dict:
        """计算 RSI 指标

        Args:
            params: {"period": 14}

        Returns:
            {"value": float, "series": list}
        """
        import talib

        close = self.df["close"].values
        rsi = talib.RSI(close, timeperiod=params["period"])

        return {
            "value": float(rsi[-1]) if not np.isnan(rsi[-1]) else 50.0,
            "series": rsi[-10:].tolist(),
        }

    def _calculate_kdj(self, params: dict) -> dict:
        """计算 KDJ 指标

        Args:
            params: {"n": 9, "m1": 3, "m2": 3}

        Returns:
            {"k": float, "d": float, "j": float, "series": dict}
        """
        import talib

        high = self.df["high"].values
        low = self.df["low"].values
        close = self.df["close"].values

        # 计算随机指标
        slowk, slowd = talib.STOCH(
            high,
            low,
            close,
            fastk_period=params["n"],
            slowk_period=params["m1"],
            slowk_matype=0,
            slowd_period=params["m2"],
            slowd_matype=0,
        )

        # KDJ 的 J 线
        j = 3 * slowk - 2 * slowd

        return {
            "k": float(slowk[-1]) if not np.isnan(slowk[-1]) else 50.0,
            "d": float(slowd[-1]) if not np.isnan(slowd[-1]) else 50.0,
            "j": float(j[-1]) if not np.isnan(j[-1]) else 50.0,
            "series": {
                "k": slowk[-10:].tolist(),
                "d": slowd[-10:].tolist(),
                "j": j[-10:].tolist(),
            },
        }

    def _calculate_boll(self, params: dict) -> dict:
        """计算布林带指标

        Args:
            params: {"period": 20, "std": 2}

        Returns:
            {"upper": float, "middle": float, "lower": float, "price": float}
        """
        import talib

        close = self.df["close"].values

        upper, middle, lower = talib.BBANDS(
            close, timeperiod=params["period"], nbdevup=params["std"], nbdevdn=params["std"]
        )

        return {
            "upper": float(upper[-1]) if not np.isnan(upper[-1]) else 0.0,
            "middle": float(middle[-1]) if not np.isnan(middle[-1]) else 0.0,
            "lower": float(lower[-1]) if not np.isnan(lower[-1]) else 0.0,
            "price": float(close[-1]),
        }

    def _calculate_ma(self, params: dict) -> dict:
        """计算均线指标

        Args:
            params: {"periods": [5, 10, 20, 60]}

        Returns:
            {"values": list[float], "periods": list[int]}
        """
        close = self.df["close"]
        periods = params["periods"]

        values = []
        for period in periods:
            if len(close) >= period:
                ma = close.rolling(window=period).mean()
                values.append(float(ma.iloc[-1]) if not np.isnan(ma.iloc[-1]) else 0.0)
            else:
                values.append(0.0)

        return {"values": values, "periods": periods}

    def _judge_macd_signal(self, macd_result: dict) -> tuple[str, int]:
        """判断 MACD 信号

        Returns:
            (signal, score): 信号描述和得分
        """
        dif = macd_result["dif"]
        dea = macd_result["dea"]
        macd = macd_result["macd"]

        # 金叉/死叉
        if dif > dea and macd > 0:
            return "金叉", 1
        elif dif < dea and macd < 0:
            return "死叉", -1
        elif macd > 0:
            return "多头", 0
        else:
            return "空头", 0

    def _judge_rsi_signal(self, rsi_result: dict) -> tuple[str, int]:
        """判断 RSI 信号

        Returns:
            (signal, score): 信号描述和得分
        """
        rsi = rsi_result["value"]

        if rsi > 80:
            return "超买", -2
        elif rsi > 70:
            return "偏强", -1
        elif rsi < 20:
            return "超卖", 2
        elif rsi < 30:
            return "偏弱", 1
        else:
            return "中性", 0

    def _judge_kdj_signal(self, kdj_result: dict) -> tuple[str, int]:
        """判断 KDJ 信号

        Returns:
            (signal, score): 信号描述和得分
        """
        k = kdj_result["k"]
        d = kdj_result["d"]
        j = kdj_result["j"]

        # 超买/超卖
        if k > 80:
            return "超买", -1
        elif k < 20:
            return "超卖", 1

        # 金叉/死叉
        if k > d:
            return "金叉", 1
        elif k < d:
            return "死叉", -1
        else:
            return "中性", 0

    def _judge_boll_signal(self, boll_result: dict) -> tuple[str, int]:
        """判断布林带信号

        Returns:
            (signal, score): 信号描述和得分
        """
        price = boll_result["price"]
        upper = boll_result["upper"]
        middle = boll_result["middle"]
        lower = boll_result["lower"]

        if price > upper:
            return "突破上轨", -1
        elif price < lower:
            return "突破下轨", 1
        elif price > middle:
            return "中轨上方", 0
        else:
            return "中轨下方", 0

    def _judge_ma_signal(self, ma_result: dict) -> tuple[str, int]:
        """判断均线信号

        Returns:
            (signal, score): 信号描述和得分
        """
        values = ma_result["values"]
        periods = ma_result["periods"]

        # 过滤掉无效值
        valid_values = [(p, v) for p, v in zip(periods, values) if v > 0]

        if len(valid_values) < 2:
            return "数据不足", 0

        # 判断多空排列
        sorted_values = [v for p, v in sorted(valid_values, key=lambda x: x[0])]
        if all(sorted_values[i] > sorted_values[i + 1] for i in range(len(sorted_values) - 1)):
            return "多头排列", 1
        elif all(sorted_values[i] < sorted_values[i + 1] for i in range(len(sorted_values) - 1)):
            return "空头排列", -1
        else:
            return "震荡", 0

    def _calculate_summary(self, signals: list) -> dict:
        """计算综合评分

        Args:
            signals: 信号列表

        Returns:
            {"total_score": int, "recommendation": str, "confidence": str}
        """
        total_score = sum(s["score"] for s in signals)

        if total_score >= 3:
            recommendation = "强烈买入"
            confidence = "高"
        elif total_score >= 1:
            recommendation = "买入"
            confidence = "中"
        elif total_score <= -3:
            recommendation = "强烈卖出"
            confidence = "高"
        elif total_score <= -1:
            recommendation = "卖出"
            confidence = "中"
        else:
            recommendation = "中性"
            confidence = "低"

        return {"total_score": total_score, "recommendation": recommendation, "confidence": confidence}

    def print_result(self, result: dict, top_n: int = 5):
        """打印精简结果

        Args:
            result: 分析结果
            top_n: 显示最近 N 天信号
        """
        print(f"\n技术指标分析 - {result['symbol']}")
        print("=" * 50)
        print(f"分析日期: {result['date']}")
        print(f"数据范围: {result['data_range']['start']} ~ {result['data_range']['end']} ({result['data_range']['days']}天)\n")

        # 指标值
        print("【指标值】")
        for indicator, values in result["indicators"].items():
            if indicator == "macd":
                print(f"MACD: DIF={values['dif']:.2f}, DEA={values['dea']:.2f}, MACD={values['macd']:.2f}")
            elif indicator == "rsi":
                print(f"RSI(14): {values['value']:.2f}")
            elif indicator == "kdj":
                print(f"KDJ: K={values['k']:.2f}, D={values['d']:.2f}, J={values['j']:.2f}")
            elif indicator == "boll":
                print(f"布林带: 上轨={values['upper']:.2f}, 中轨={values['middle']:.2f}, 下轨={values['lower']:.2f}")
            elif indicator == "ma":
                periods = result["indicators"]["ma"]["periods"]
                values_list = result["indicators"]["ma"]["values"]
                ma_str = ", ".join([f"MA{p}={v:.2f}" for p, v in zip(periods, values_list)])
                print(f"均线: {ma_str}")

        print()

        # 信号判断
        print("【信号判断】")
        for signal in result["signals"]:
            score_str = f"+{signal['score']}" if signal["score"] > 0 else str(signal["score"])
            print(f"{signal['indicator'].upper()}: {signal['signal']} ({score_str})")

        print()

        # 综合建议
        summary = result["summary"]
        print("【综合建议】")
        score_str = f"+{summary['total_score']}" if summary["total_score"] > 0 else str(summary["total_score"])
        print(f"总评分: {score_str}")
        print(f"建议: {summary['recommendation']} ({summary['confidence']}置信度)\n")


async def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="技术指标分析")
    parser.add_argument("symbol", help="股票代码")
    parser.add_argument("--days", type=int, default=60, help="历史天数（默认 60）")
    parser.add_argument("--indicators", help="指标列表（逗号分隔，默认全部）")
    parser.add_argument("--params", help="指标参数（JSON 格式）")
    parser.add_argument("--top-n", type=int, default=5, help="显示最近 N 天信号（默认 5）")

    args = parser.parse_args()

    # 解析指标列表
    indicators = None
    if args.indicators:
        indicators = [i.strip() for i in args.indicators.split(",")]

    # 解析参数
    params = None
    if args.params:
        params = json.loads(args.params)

    # 分析
    processor = IndicatorProcessor(args.symbol, args.days)
    result = await processor.analyze(indicators=indicators, params=params)

    # 打印精简结果
    processor.print_result(result, args.top_n)

    # 保存完整结果到文件
    output_path = get_output_path(
        "technical_indicators", "indicator_analysis", result["date"], ext="json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"完整结果已保存到: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
