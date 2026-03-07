# -*- coding: utf-8 -*-
"""风险分析 Processor"""

import argparse
import asyncio
import json
from datetime import datetime, timedelta
from typing import Any

import akshare as ak

from openclaw_alpha.core.processor_utils import get_output_path


class RiskProcessor:
    """风险分析处理器"""

    # 风险类型
    HIGH_RISK = "高"
    MEDIUM_RISK = "中"
    LOW_RISK = "低"
    NORMAL = "正常"

    # 价格风险阈值
    PRICE_HIGH_RISK_THRESHOLD = 9.0  # 单日跌幅 >= 9%
    PRICE_MEDIUM_RISK_DAYS = 3  # 连续下跌天数
    PRICE_MEDIUM_RISK_PCT = 10.0  # 累计跌幅

    # 资金风险阈值（单位：亿）
    FLOW_HIGH_RISK_THRESHOLD = 5.0  # 单日净流出 >= 5亿
    FLOW_MEDIUM_RISK_DAYS = 3  # 连续流出天数
    FLOW_MEDIUM_RISK_AMOUNT = 1.0  # 累计流出

    def __init__(self, symbol: str, date: str | None = None, days: int = 5):
        """
        初始化

        Args:
            symbol: 股票代码（6位数字）
            date: 检查日期，格式 YYYY-MM-DD
            days: 检查近 N 天
        """
        self.symbol = symbol.zfill(6)
        self.date = date or datetime.now().strftime("%Y-%m-%d")
        self.days = days

    async def check(self) -> dict[str, Any]:
        """
        检查个股风险

        Returns:
            风险检查结果
        """
        # 1. 检查业绩风险
        forecast_risk = await self._check_forecast_risk()

        # 2. 检查价格风险
        price_risk = await self._check_price_risk()

        # 3. 检查资金风险
        flow_risk = await self._check_flow_risk()

        # 4. 综合评级
        risks = []
        if forecast_risk:
            risks.append(forecast_risk)
        if price_risk:
            risks.append(price_risk)
        if flow_risk:
            risks.append(flow_risk)

        rating = self._calculate_rating(risks)
        suggestions = self._generate_suggestions(risks)

        # 5. 输出结果
        result = {
            "code": self.symbol,
            "name": await self._get_stock_name(),
            "date": self.date,
            "rating": rating,
            "risks": risks,
            "suggestions": suggestions,
        }

        return result

    async def _check_forecast_risk(self) -> dict[str, Any] | None:
        """检查业绩风险"""
        try:
            from skills.risk_alert.scripts.forecast_fetcher import fetch

            records = await fetch()

            # 筛选该股票的业绩预告
            stock_records = [r for r in records if r["code"] == self.symbol]

            if not stock_records:
                return None

            # 取最新的预告
            latest = stock_records[0]

            if latest["risk_level"] == self.HIGH_RISK:
                return {
                    "type": "业绩风险",
                    "level": self.HIGH_RISK,
                    "detail": f"业绩{latest['forecast_type']}，预计变动 {latest['change_pct']:.1f}%",
                }
            elif latest["risk_level"] == self.MEDIUM_RISK:
                return {
                    "type": "业绩风险",
                    "level": self.MEDIUM_RISK,
                    "detail": f"业绩{latest['forecast_type']}，预计变动 {latest['change_pct']:.1f}%",
                }

            return None
        except Exception as e:
            print(f"业绩风险检查失败: {e}")
            return None

    async def _check_price_risk(self) -> dict[str, Any] | None:
        """检查价格风险"""
        try:
            # 获取近 N 天的日线数据
            end_date = datetime.strptime(self.date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=self.days + 10)  # 多取几天以确保有足够数据

            df = ak.stock_zh_a_hist(
                symbol=self.symbol,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq",
            )

            if df.empty or len(df) < self.days:
                return None

            # 取最近 N 天
            recent = df.tail(self.days)

            # 检查单日大幅下跌
            for _, row in recent.iterrows():
                if row["涨跌幅"] <= -self.PRICE_HIGH_RISK_THRESHOLD:
                    return {
                        "type": "价格风险",
                        "level": self.HIGH_RISK,
                        "detail": f"单日大跌 {abs(row['涨跌幅']):.2f}%",
                    }

            # 检查连续下跌
            down_days = 0
            total_change = 0.0
            for _, row in recent.iterrows():
                if row["涨跌幅"] < 0:
                    down_days += 1
                    total_change += row["涨跌幅"]
                else:
                    break  # 连续下跌中断

            if down_days >= self.PRICE_MEDIUM_RISK_DAYS and abs(total_change) >= self.PRICE_MEDIUM_RISK_PCT:
                return {
                    "type": "价格风险",
                    "level": self.MEDIUM_RISK,
                    "detail": f"连续下跌 {down_days} 天，累计跌幅 {abs(total_change):.2f}%",
                }

            return None
        except Exception as e:
            print(f"价格风险检查失败: {e}")
            return None

    async def _check_flow_risk(self) -> dict[str, Any] | None:
        """检查资金风险"""
        try:
            # 判断市场（深市/沪市）
            market = "sz" if self.symbol.startswith(("0", "3")) else "sh"

            # 获取资金流向数据
            df = ak.stock_individual_fund_flow(stock=self.symbol, market=market)

            if df.empty or len(df) < self.days:
                return None

            # 取最近 N 天
            recent = df.head(self.days)

            # 检查单日大额流出（主力净流入）
            for _, row in recent.iterrows():
                net_amount = row["主力净流入-净额"]
                if net_amount <= -self.FLOW_HIGH_RISK_THRESHOLD * 1e8:
                    return {
                        "type": "资金风险",
                        "level": self.HIGH_RISK,
                        "detail": f"单日主力净流出 {abs(net_amount) / 1e8:.2f} 亿",
                    }

            # 检查连续流出
            outflow_days = 0
            total_outflow = 0.0
            for _, row in recent.iterrows():
                net_amount = row["主力净流入-净额"]
                if net_amount < 0:
                    outflow_days += 1
                    total_outflow += abs(net_amount)
                else:
                    break  # 连续流出中断

            if (
                outflow_days >= self.FLOW_MEDIUM_RISK_DAYS
                and total_outflow >= self.FLOW_MEDIUM_RISK_AMOUNT * 1e8
            ):
                return {
                    "type": "资金风险",
                    "level": self.MEDIUM_RISK,
                    "detail": f"连续 {outflow_days} 天主力净流出，累计 {total_outflow / 1e8:.2f} 亿",
                }

            return None
        except Exception as e:
            print(f"资金风险检查失败: {e}")
            return None

    def _calculate_rating(self, risks: list[dict[str, Any]]) -> str:
        """计算综合评级"""
        if not risks:
            return self.NORMAL

        levels = [r["level"] for r in risks]

        if self.HIGH_RISK in levels:
            return self.HIGH_RISK
        elif self.MEDIUM_RISK in levels:
            return self.MEDIUM_RISK
        else:
            return self.LOW_RISK

    def _generate_suggestions(self, risks: list[dict[str, Any]]) -> list[str]:
        """生成建议"""
        if not risks:
            return ["暂无明显风险信号"]

        suggestions = []

        # 业绩风险建议
        if any(r["type"] == "业绩风险" for r in risks):
            suggestions.append("关注业绩公告详情")
            suggestions.append("评估业绩对股价的潜在影响")

        # 价格风险建议
        if any(r["type"] == "价格风险" for r in risks):
            suggestions.append("关注下跌原因（基本面/技术面）")
            suggestions.append("评估持仓比例和风险承受能力")

        # 资金风险建议
        if any(r["type"] == "资金风险" for r in risks):
            suggestions.append("关注主力资金动向")
            suggestions.append("判断资金流出是短期调整还是长期趋势")

        # 通用建议
        if len(risks) >= 2:
            suggestions.append("多风险叠加，建议谨慎")

        return suggestions

    async def _get_stock_name(self) -> str:
        """获取股票名称"""
        try:
            # 从业绩预告数据中查找
            from skills.risk_alert.scripts.forecast_fetcher import fetch

            records = await fetch()
            for r in records:
                if r["code"] == self.symbol:
                    return r["name"]

            # 如果没找到，返回代码
            return self.symbol
        except Exception:
            return self.symbol


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="风险检查")
    parser.add_argument("symbol", help="股票代码（6位数字）")
    parser.add_argument("--date", default=None, help="检查日期（YYYY-MM-DD）")
    parser.add_argument("--days", type=int, default=5, help="检查近 N 天")
    parser.add_argument("--output", action="store_true", help="保存到文件")
    return parser.parse_args()


async def main():
    args = parse_args()

    processor = RiskProcessor(symbol=args.symbol, date=args.date, days=args.days)
    result = await processor.check()

    # 打印结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 保存到文件
    if args.output:
        output_path = get_output_path("risk_alert", "risk_check", args.date or datetime.now().strftime("%Y-%m-%d"))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
