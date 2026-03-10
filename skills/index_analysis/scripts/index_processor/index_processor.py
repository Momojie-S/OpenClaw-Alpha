# -*- coding: utf-8 -*-
"""指数分析处理器"""

import argparse
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from openclaw_alpha.core.processor_utils import get_output_path

from ..index_fetcher import fetch

logger = logging.getLogger(__name__)

# 核心指数配置
CORE_INDICES = [
    {"name": "上证指数", "code": "sh000001", "type": "主板"},
    {"name": "深证成指", "code": "sz399001", "type": "主板"},
    {"name": "沪深300", "code": "sh000300", "type": "主板"},
    {"name": "创业板指", "code": "sz399006", "type": "成长"},
    {"name": "科创50", "code": "sh000688", "type": "成长"},
    {"name": "中证500", "code": "sh000905", "type": "中盘"},
]

SKILL_NAME = "index_analysis"
PROCESSOR_NAME = "index"


class IndexProcessor:
    """指数分析处理器"""

    def __init__(self, date: str, top_n: int = 6):
        """
        初始化处理器。

        Args:
            date: 分析日期（YYYY-MM-DD）
            top_n: 返回指数数量
        """
        self.date = date
        self.top_n = top_n

    def _calc_ma(self, data: list[dict], period: int) -> float | None:
        """
        计算均线。

        Args:
            data: 行情数据（已按日期排序，旧到新）
            period: 均线周期

        Returns:
            均线值，数据不足时返回 None
        """
        if len(data) < period:
            return None

        recent = data[-period:]
        return sum(d["close"] for d in recent) / period

    def _judge_trend(self, close: float, ma5: float | None, ma20: float | None, change_pct: float) -> str:
        """
        判断趋势。

        Args:
            close: 收盘价
            ma5: 5日均线
            ma20: 20日均线
            change_pct: 涨跌幅

        Returns:
            趋势状态
        """
        # 数据不足时无法判断
        if ma5 is None or ma20 is None:
            return "数据不足"

        # 先判断震荡（均线接近，涨跌幅小）
        if abs(ma5 - ma20) / ma20 < 0.01 and abs(change_pct) < 1:
            return "震荡"
        elif close > ma5 > ma20 and change_pct > 1:
            return "强势上涨"
        elif ma5 > ma20 and 0 < change_pct <= 1:
            return "震荡上涨"
        elif ma5 < ma20 and -1 <= change_pct < 0:
            return "震荡下跌"
        elif close < ma5 < ma20 and change_pct < -1:
            return "弱势下跌"
        else:
            return "震荡"

    def _calc_market_temperature(self, indices: list[dict]) -> str:
        """
        计算市场温度。

        Args:
            indices: 指数列表

        Returns:
            市场温度
        """
        changes = [i.get("change_pct", 0) for i in indices]

        up_count = sum(1 for c in changes if c > 2)
        warm_count = sum(1 for c in changes if c > 1)
        down_count = sum(1 for c in changes if c < -2)
        cold_count = sum(1 for c in changes if c < -1)

        if up_count >= 3:
            return "过热"
        elif warm_count >= 2:
            return "温热"
        elif down_count >= 3:
            return "过冷"
        elif cold_count >= 2:
            return "偏冷"
        else:
            return "正常"

    def _calc_overall_trend(self, indices: list[dict]) -> str:
        """
        计算整体趋势。

        Args:
            indices: 指数列表

        Returns:
            整体趋势
        """
        trends = [i.get("trend", "震荡") for i in indices]

        # 统计各种趋势数量
        up_count = sum(1 for t in trends if "上涨" in t)
        down_count = sum(1 for t in trends if "下跌" in t)

        if up_count >= 4:
            return "强势"
        elif up_count >= 2:
            return "偏强"
        elif down_count >= 4:
            return "弱势"
        elif down_count >= 2:
            return "偏弱"
        else:
            return "震荡"

    def _format_number(self, value: float, divisor: float = 1, unit: str = "") -> str:
        """
        格式化数字。

        Args:
            value: 数值
            divisor: 除数
            unit: 单位

        Returns:
            格式化后的字符串
        """
        if value == 0:
            return "0"

        divided = value / divisor
        if divided >= 10000:
            return f"{divided / 10000:.1f}万{unit}"
        elif divided >= 100:
            return f"{divided:.0f}{unit}"
        else:
            return f"{divided:.1f}{unit}"

    async def process(self) -> dict[str, Any]:
        """
        执行指数分析。

        Returns:
            分析结果
        """
        # 计算需要的日期范围（获取30天数据用于计算MA20）
        end_date_dt = datetime.strptime(self.date, "%Y-%m-%d")
        start_date_dt = end_date_dt - timedelta(days=60)  # 多取一些以确保有足够的交易日
        start_date = start_date_dt.strftime("%Y%m%d")
        end_date = end_date_dt.strftime("%Y%m%d")

        # 获取所有指数数据
        indices_data = []
        for index_config in CORE_INDICES[:self.top_n]:
            try:
                data = await fetch(
                    symbol=index_config["code"],
                    start_date=start_date,
                    end_date=end_date,
                )

                if not data:
                    logger.warning(f"指数 {index_config['name']} 无数据")
                    continue

                # 找到目标日期的数据
                target_data = None
                for d in data:
                    if d["date"] == self.date:
                        target_data = d
                        break

                # 如果没有目标日期，使用最新数据
                if target_data is None:
                    target_data = data[-1]
                    logger.info(f"指数 {index_config['name']} 使用最新数据: {target_data['date']}")

                # 计算均线
                ma5 = self._calc_ma(data, 5)
                ma20 = self._calc_ma(data, 20)

                # 计算涨跌幅（与前一日对比）
                change_pct = 0.0
                change_points = 0.0
                prev_close = None
                if len(data) >= 2:
                    for i, d in enumerate(data):
                        if d["date"] == target_data["date"] and i > 0:
                            prev_close = data[i - 1]["close"]
                            break

                    if prev_close and prev_close > 0:
                        change_points = target_data["close"] - prev_close
                        change_pct = (change_points / prev_close) * 100

                # 判断趋势
                trend = self._judge_trend(target_data["close"], ma5, ma20, change_pct)

                index_item = {
                    "name": index_config["name"],
                    "code": index_config["code"],
                    "type": index_config["type"],
                    "date": target_data["date"],
                    "close": round(target_data["close"], 2),
                    "change_pct": round(change_pct, 2),
                    "change_points": round(change_points, 2),
                    "open": round(target_data["open"], 2),
                    "high": round(target_data["high"], 2),
                    "low": round(target_data["low"], 2),
                    "volume": self._format_number(target_data["volume"], 100000000, "股"),
                    "amount": self._format_number(target_data["amount"], 100000000, "元"),
                    "ma5": round(ma5, 2) if ma5 else None,
                    "ma20": round(ma20, 2) if ma20 else None,
                    "trend": trend,
                }
                indices_data.append(index_item)

            except Exception as e:
                logger.error(f"获取指数 {index_config['name']} 失败: {e}")
                continue

        if not indices_data:
            return {
                "date": self.date,
                "error": "无法获取任何指数数据",
            }

        # 按涨跌幅排序
        indices_data.sort(key=lambda x: x["change_pct"], reverse=True)

        # 计算市场温度
        temperature = self._calc_market_temperature(indices_data)

        # 计算整体趋势
        overall_trend = self._calc_overall_trend(indices_data)

        # 找出最强和最弱指数
        strongest = indices_data[0] if indices_data else None
        weakest = indices_data[-1] if indices_data else None

        result = {
            "date": self.date,
            "market_temperature": temperature,
            "overall_trend": overall_trend,
            "strongest": {
                "name": strongest["name"],
                "change_pct": strongest["change_pct"],
            } if strongest else None,
            "weakest": {
                "name": weakest["name"],
                "change_pct": weakest["change_pct"],
            } if weakest else None,
            "indices": indices_data,
        }

        # 保存完整数据到文件
        output_path = get_output_path(SKILL_NAME, PROCESSOR_NAME, self.date, ext="json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"完整数据已保存到: {output_path}")

        return result


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="指数分析")
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="分析日期（YYYY-MM-DD），默认今天",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=6,
        help="返回指数数量，默认6个",
    )
    return parser.parse_args()


async def main():
    """主函数"""
    args = parse_args()

    processor = IndexProcessor(date=args.date, top_n=args.top_n)
    result = await processor.process()

    # 输出精简结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
