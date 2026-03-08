# -*- coding: utf-8 -*-
"""市场择时处理器"""

import argparse
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from openclaw_alpha.core.processor_utils import get_output_path, load_output


class MarketTimingProcessor:
    """市场择时处理器

    整合多个情绪指标，生成情绪综合指数和择时信号。
    """

    def __init__(self):
        """初始化"""
        self.skill_name = "market_sentiment"
        self.processor_name = "timing"

    def _normalize_value(
        self, value: float, min_val: float, max_val: float, reverse: bool = False
    ) -> float:
        """
        标准化数值到 0-100 范围

        Args:
            value: 原始值
            min_val: 最小值
            max_val: 最大值
            reverse: 是否反转（用于负向指标）

        Returns:
            标准化后的值（0-100）
        """
        if max_val == min_val:
            return 50

        normalized = (value - min_val) / (max_val - min_val) * 100
        normalized = max(0, min(100, normalized))

        if reverse:
            normalized = 100 - normalized

        return normalized

    def _calc_limit_ratio_score(self, limit_up: int, limit_down: int) -> float:
        """
        计算涨跌停比得分

        Args:
            limit_up: 涨停数
            limit_down: 跌停数

        Returns:
            涨跌停比得分（0-100）
        """
        if limit_down == 0:
            # 没有跌停，用涨停数直接映射
            return min(100, limit_up / 2)

        ratio = limit_up / limit_down

        # 比率映射：0 -> 0, 1 -> 50, 3 -> 75, 10 -> 100
        if ratio <= 1:
            score = ratio * 50
        elif ratio <= 3:
            score = 50 + (ratio - 1) * 12.5
        else:
            score = 75 + min(25, (ratio - 3) * 3.57)

        return min(100, score)

    def _calc_trend_ratio_score(self, up: int, down: int) -> float:
        """
        计算涨跌家数比得分

        Args:
            up: 上涨家数
            down: 下跌家数

        Returns:
            涨跌家数比得分（0-100）
        """
        total = up + down
        if total == 0:
            return 50

        up_ratio = up / total
        # 比率映射：0% -> 0, 50% -> 50, 100% -> 100
        return up_ratio * 100

    def _calc_flow_score(self, flow_pct: float) -> float:
        """
        计算资金流向得分

        Args:
            flow_pct: 主力净流入占比

        Returns:
            资金流向得分（0-100）
        """
        # 资金流入占比通常在 -2% 到 2% 之间
        return self._normalize_value(flow_pct, -2, 2)

    def _calc_sentiment_index(
        self,
        temperature: int,
        limit_score: float,
        trend_score: float,
        flow_score: float,
        breadth_score: Optional[float] = None,
    ) -> float:
        """
        计算情绪综合指数

        Args:
            temperature: 市场温度
            limit_score: 涨跌停比得分
            trend_score: 涨跌家数比得分
            flow_score: 资金流向得分
            breadth_score: 市场宽度得分（可选）

        Returns:
            情绪综合指数（0-100）
        """
        if breadth_score is not None:
            # 有宽度数据时的权重
            weighted_score = (
                temperature * 0.25
                + limit_score * 0.20
                + trend_score * 0.15
                + flow_score * 0.15
                + breadth_score * 0.25
            )
        else:
            # 无宽度数据时的权重
            weighted_score = (
                temperature * 0.35
                + limit_score * 0.25
                + trend_score * 0.20
                + flow_score * 0.20
            )

        return round(weighted_score, 1)

    def _determine_zone(self, sentiment_index: float) -> str:
        """
        判断情绪分区

        Args:
            sentiment_index: 情绪综合指数

        Returns:
            情绪分区
        """
        if sentiment_index < 25:
            return "极度低迷"
        elif sentiment_index < 40:
            return "低迷"
        elif sentiment_index < 60:
            return "中性"
        elif sentiment_index < 75:
            return "高涨"
        else:
            return "极度高涨"

    def _determine_left_signal(self, sentiment_index: float) -> dict:
        """
        判断左侧择时信号

        Args:
            sentiment_index: 情绪综合指数

        Returns:
            左侧择时信号
        """
        if sentiment_index < 20:
            return {
                "signal": "强买入",
                "description": "情绪极度低迷，左侧强买入信号",
            }
        elif sentiment_index < 30:
            return {
                "signal": "买入",
                "description": "情绪低迷，左侧买入信号",
            }
        elif sentiment_index > 80:
            return {
                "signal": "强卖出",
                "description": "情绪极度高涨，左侧强卖出信号",
            }
        elif sentiment_index > 70:
            return {
                "signal": "卖出",
                "description": "情绪高涨，左侧卖出信号",
            }
        else:
            return {
                "signal": "持有",
                "description": "情绪中性，持有观望",
            }

    def _determine_right_signal(
        self, sentiment_index: float, prev_index: Optional[float] = None
    ) -> dict:
        """
        判断右侧择时信号

        Args:
            sentiment_index: 当日情绪综合指数
            prev_index: 前一日情绪综合指数

        Returns:
            右侧择时信号
        """
        if prev_index is None:
            return {
                "signal": "等待",
                "description": "数据不足，等待更多数据",
            }

        change = sentiment_index - prev_index
        change_pct = change / prev_index * 100 if prev_index > 0 else 0

        # 趋势判断
        if change_pct > 15:
            return {
                "signal": "买入",
                "description": f"情绪快速上升（+{change_pct:.1f}%），右侧买入信号",
            }
        elif change_pct > 5:
            return {
                "signal": "偏多",
                "description": f"情绪上升（+{change_pct:.1f}%），右侧偏多信号",
            }
        elif change_pct < -15:
            return {
                "signal": "卖出",
                "description": f"情绪快速下降（{change_pct:.1f}%），右侧卖出信号",
            }
        elif change_pct < -5:
            return {
                "signal": "偏空",
                "description": f"情绪下降（{change_pct:.1f}%），右侧偏空信号",
            }
        else:
            return {
                "signal": "持有",
                "description": "情绪平稳，持有观望",
            }

    def _generate_recommendation(
        self,
        zone: str,
        left_signal: dict,
        right_signal: dict,
        sentiment_index: float,
    ) -> str:
        """
        生成投资建议

        Args:
            zone: 情绪分区
            left_signal: 左侧信号
            right_signal: 右侧信号
            sentiment_index: 情绪综合指数

        Returns:
            投资建议
        """
        recommendations = []

        # 基于分区
        if zone == "极度低迷":
            recommendations.append("市场情绪极度低迷，可能是中长期布局良机")
            recommendations.append("建议关注价值股、高股息股")
        elif zone == "低迷":
            recommendations.append("市场情绪偏低，适合分批建仓")
        elif zone == "高涨":
            recommendations.append("市场情绪偏高，注意风险控制")
            recommendations.append("建议逐步减仓，避免追高")
        elif zone == "极度高涨":
            recommendations.append("市场情绪极度亢奋，注意风险")
            recommendations.append("建议降低仓位，等待回调")

        # 基于信号
        if left_signal["signal"] in ["强买入", "买入"]:
            recommendations.append(f"左侧信号：{left_signal['description']}")
        elif left_signal["signal"] in ["强卖出", "卖出"]:
            recommendations.append(f"左侧信号：{left_signal['description']}")

        if right_signal["signal"] in ["买入", "偏多"]:
            recommendations.append(f"右侧信号：{right_signal['description']}")
        elif right_signal["signal"] in ["卖出", "偏空"]:
            recommendations.append(f"右侧信号：{right_signal['description']}")

        return "；".join(recommendations) if recommendations else "市场情绪中性，正常操作"

    async def process(self, date: str = None, days: int = 5) -> dict:
        """
        处理市场择时分析

        Args:
            date: 日期，格式 YYYY-MM-DD
            days: 回溯天数（用于计算趋势）

        Returns:
            市场择时分析结果
        """
        date = date or datetime.now().strftime("%Y-%m-%d")

        # 1. 读取当日情绪数据
        sentiment_data = load_output(
            self.skill_name, "sentiment", date, ext="json"
        )

        if not sentiment_data:
            return {
                "date": date,
                "error": "未找到当日情绪数据，请先运行 sentiment_processor",
            }

        # 2. 读取当日宽度数据（可选）
        breadth_data = load_output(
            self.skill_name, "breadth", date, ext="json"
        )

        # 3. 计算各维度得分
        temperature = sentiment_data["sentiment"]["temperature"]

        limit_score = self._calc_limit_ratio_score(
            sentiment_data["limit"]["up"],
            sentiment_data["limit"]["down"],
        )

        trend_score = self._calc_trend_ratio_score(
            sentiment_data["trend"]["up"],
            sentiment_data["trend"]["down"],
        )

        flow_score = self._calc_flow_score(
            sentiment_data["flow"]["main_net_inflow_pct"]
        )

        breadth_score = None
        if breadth_data and "breadth" in breadth_data:
            breadth_score = breadth_data["breadth"].get("ratio_20d", 50)

        # 4. 计算情绪综合指数
        sentiment_index = self._calc_sentiment_index(
            temperature, limit_score, trend_score, flow_score, breadth_score
        )

        # 5. 读取前一日数据（用于右侧信号）
        prev_date = (
            datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)
        ).strftime("%Y-%m-%d")
        prev_sentiment_data = load_output(
            self.skill_name, "sentiment", prev_date, ext="json"
        )

        prev_index = None
        if prev_sentiment_data:
            # 计算前一日情绪指数（简化版，只用温度）
            prev_index = prev_sentiment_data["sentiment"]["temperature"]

        # 6. 判断择时信号
        zone = self._determine_zone(sentiment_index)
        left_signal = self._determine_left_signal(sentiment_index)
        right_signal = self._determine_right_signal(sentiment_index, prev_index)
        recommendation = self._generate_recommendation(
            zone, left_signal, right_signal, sentiment_index
        )

        # 7. 构建结果
        result = {
            "date": date,
            "sentiment_index": sentiment_index,
            "zone": zone,
            "signals": {
                "left": left_signal,
                "right": right_signal,
            },
            "recommendation": recommendation,
            "components": {
                "temperature": temperature,
                "limit_score": round(limit_score, 1),
                "trend_score": round(trend_score, 1),
                "flow_score": round(flow_score, 1),
                "breadth_score": round(breadth_score, 1) if breadth_score else None,
            },
            "weights": {
                "temperature": 0.25 if breadth_score else 0.35,
                "limit_score": 0.20 if breadth_score else 0.25,
                "trend_score": 0.15 if breadth_score else 0.20,
                "flow_score": 0.15 if breadth_score else 0.20,
                "breadth_score": 0.25 if breadth_score else 0,
            },
        }

        # 8. 保存完整数据到文件
        output_path = get_output_path(
            self.skill_name, self.processor_name, date, ext="json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="市场择时分析")
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="分析日期，格式 YYYY-MM-DD，默认今天",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=5,
        help="回溯天数，用于计算趋势，默认 5 天",
    )
    return parser.parse_args()


async def main():
    """主入口"""
    args = parse_args()
    processor = MarketTimingProcessor()
    result = await processor.process(date=args.date, days=args.days)

    # 输出精简结果
    output = {
        "date": result["date"],
        "sentiment_index": result["sentiment_index"],
        "zone": result["zone"],
        "signals": result["signals"],
        "recommendation": result["recommendation"],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
