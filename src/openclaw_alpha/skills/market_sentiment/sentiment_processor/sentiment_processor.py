# -*- coding: utf-8 -*-
"""市场情绪分析处理器"""

import argparse
import asyncio
import json
from datetime import datetime

from openclaw_alpha.core.processor_utils import get_output_path

from openclaw_alpha.skills.market_sentiment.limit_fetcher import fetch as fetch_limit
from openclaw_alpha.skills.market_sentiment.flow_fetcher import fetch as fetch_flow


class MarketSentimentProcessor:
    """市场情绪分析处理器"""

    def __init__(self):
        """初始化"""
        self.skill_name = "market_sentiment"
        self.processor_name = "sentiment"

    async def _fetch_trend_data(self, date: str) -> dict:
        """
        获取涨跌家数数据

        使用 Tushare daily 接口统计涨跌家数

        Args:
            date: 日期，格式 YYYY-MM-DD

        Returns:
            涨跌家数统计
        """
        import tushare as ts
        import os

        pro = ts.pro_api(os.getenv("TUSHARE_TOKEN"))
        date_str = date.replace("-", "")

        # 获取当日行情
        df = pro.daily(trade_date=date_str)

        if df.empty:
            return {
                "up": 0,
                "down": 0,
                "flat": 0,
                "total": 0,
            }

        # 统计涨跌
        up = len(df[df["pct_chg"] > 0])
        down = len(df[df["pct_chg"] < 0])
        flat = len(df[df["pct_chg"] == 0])

        return {
            "up": up,
            "down": down,
            "flat": flat,
            "total": len(df),
        }

    def _calculate_temperature(
        self, limit_data: dict, trend_data: dict, flow_data: dict
    ) -> int:
        """
        计算市场温度

        Args:
            limit_data: 涨跌停数据
            trend_data: 涨跌家数数据
            flow_data: 资金流向数据

        Returns:
            市场温度（0-100）
        """
        # 涨停维度（0-100）
        limit_up = limit_data.get("limit_up", 0)
        if limit_up > 200:
            limit_score = 100
        elif limit_up > 100:
            limit_score = 80
        elif limit_up > 50:
            limit_score = 60
        elif limit_up > 20:
            limit_score = 40
        else:
            limit_score = 20

        # 涨跌家数维度（0-100）
        total = trend_data.get("total", 1)
        up = trend_data.get("up", 0)
        trend_score = (up / total) * 100 if total > 0 else 50

        # 资金流向维度（0-100）
        main_pct = flow_data.get("main_net_inflow_pct", 0)
        if main_pct > 1:
            flow_score = 100
        elif main_pct > 0.5:
            flow_score = 80
        elif main_pct > 0:
            flow_score = 60
        elif main_pct > -0.5:
            flow_score = 40
        else:
            flow_score = 20

        # 加权平均
        temperature = limit_score * 0.3 + trend_score * 0.4 + flow_score * 0.3

        return int(temperature)

    def _determine_status(self, temperature: int) -> str:
        """
        判断市场情绪状态

        Args:
            temperature: 市场温度

        Returns:
            情绪状态
        """
        if temperature >= 80:
            return "极度亢奋"
        elif temperature >= 60:
            return "偏热"
        elif temperature >= 40:
            return "正常"
        elif temperature >= 20:
            return "偏冷"
        else:
            return "极度恐慌"

    def _identify_signals(
        self, limit_data: dict, flow_data: dict, temperature: int
    ) -> list[str]:
        """
        识别极端信号

        Args:
            limit_data: 涨跌停数据
            flow_data: 资金流向数据
            temperature: 市场温度

        Returns:
            信号列表
        """
        signals = []

        # 过热预警
        if limit_data.get("limit_up", 0) > 200 or temperature > 90:
            signals.append("过热预警")

        # 恐慌底部
        if limit_data.get("limit_down", 0) > 100 or temperature < 10:
            signals.append("恐慌底部")

        # 主力流出
        if flow_data.get("main_net_inflow_pct", 0) < -1:
            signals.append("主力大幅流出")

        # 分化严重
        if (
            limit_data.get("limit_up", 0) > 50
            and limit_data.get("limit_down", 0) > 20
        ):
            signals.append("分化严重")

        return signals

    async def process(self, date: str = None) -> dict:
        """
        处理市场情绪分析

        Args:
            date: 日期，格式 YYYY-MM-DD

        Returns:
            市场情绪分析结果
        """
        date = date or datetime.now().strftime("%Y-%m-%d")

        # 1. 获取涨跌停数据
        limit_data = await fetch_limit(date=date)

        # 2. 获取资金流向
        flow_data = await fetch_flow(date=date)

        # 3. 获取涨跌家数
        trend_data = await self._fetch_trend_data(date=date)

        # 4. 计算市场温度
        temperature = self._calculate_temperature(limit_data, trend_data, flow_data)

        # 5. 判断市场状态
        status = self._determine_status(temperature)

        # 6. 识别极端信号
        signals = self._identify_signals(limit_data, flow_data, temperature)

        # 7. 构建结果
        result = {
            "date": date,
            "limit": {
                "up": limit_data["limit_up"],
                "down": limit_data["limit_down"],
                "break_board": limit_data.get("break_board", 0),
            },
            "trend": {
                "up": trend_data["up"],
                "down": trend_data["down"],
                "flat": trend_data["flat"],
            },
            "flow": {
                "main_net_inflow": flow_data["main_net_inflow"],
                "main_net_inflow_pct": flow_data["main_net_inflow_pct"],
            },
            "sentiment": {
                "temperature": temperature,
                "status": status,
                "signals": signals,
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
    parser = argparse.ArgumentParser(description="市场情绪分析")
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="分析日期，格式 YYYY-MM-DD，默认今天",
    )
    return parser.parse_args()


async def main():
    """主入口"""
    args = parse_args()
    processor = MarketSentimentProcessor()
    result = await processor.process(date=args.date)

    # 输出精简结果
    output = {
        "date": result["date"],
        "limit": result["limit"],
        "trend": result["trend"],
        "sentiment": result["sentiment"],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
