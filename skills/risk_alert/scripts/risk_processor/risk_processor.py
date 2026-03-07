# -*- coding: utf-8 -*-
"""风险分析 Processor

支持单个股票和批量风险检查。
批量检查可以从命令行、文件或 watchlist_monitor 自选股读取股票列表。
"""

import argparse
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import akshare as ak

from openclaw_alpha.core.processor_utils import get_output_path, load_output


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

    # 单股检查
    parser.add_argument("symbol", nargs="?", help="股票代码（6位数字）")

    # 日期和天数
    parser.add_argument("--date", default=None, help="检查日期（YYYY-MM-DD）")
    parser.add_argument("--days", type=int, default=5, help="检查近 N 天")

    # 批量检查
    parser.add_argument("--batch", help="批量检查（逗号分隔的股票代码）")
    parser.add_argument("--batch-file", help="从文件读取股票列表（每行一个代码）")
    parser.add_argument("--watchlist", action="store_true", help="从自选股列表读取")

    # 输出
    parser.add_argument("--output", action="store_true", help="保存到文件")
    parser.add_argument("--top-n", type=int, default=10, help="每个风险等级显示数量")

    return parser.parse_args()


def get_stock_list(args) -> list[str] | None:
    """
    从命令行参数获取股票列表

    Args:
        args: 命令行参数

    Returns:
        股票代码列表，如果只有一个股票则返回 None
    """
    symbols = []

    # 从 --batch 参数读取
    if args.batch:
        symbols.extend([s.strip() for s in args.batch.split(",") if s.strip()])

    # 从文件读取
    if args.batch_file:
        file_path = Path(args.batch_file)
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    code = line.strip()
                    if code and not code.startswith("#"):
                        symbols.append(code)

    # 从 watchlist 读取
    if args.watchlist:
        watchlist_data = load_output("watchlist_monitor", "watchlist")
        if watchlist_data and "codes" in watchlist_data:
            symbols.extend(watchlist_data["codes"])

    # 去重
    symbols = list(dict.fromkeys(symbols))

    return symbols if symbols else None


async def batch_check(symbols: list[str], date: str | None, days: int) -> dict[str, Any]:
    """
    批量检查股票风险

    Args:
        symbols: 股票代码列表
        date: 检查日期
        days: 检查近 N 天

    Returns:
        批量检查结果
    """
    check_date = date or datetime.now().strftime("%Y-%m-%d")

    # 按风险等级分组
    grouped = {
        "高风险": [],
        "中风险": [],
        "低风险": [],
        "正常": [],
    }

    # 并发检查所有股票
    tasks = [RiskProcessor(symbol=s, date=check_date, days=days).check() for s in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # 检查失败
            grouped["正常"].append({
                "code": symbols[i],
                "name": symbols[i],
                "rating": "正常",
                "error": str(result),
            })
        else:
            rating = result.get("rating", "正常")
            if rating in grouped:
                grouped[rating].append(result)

    # 统计
    summary = {level: len(items) for level, items in grouped.items()}

    return {
        "date": check_date,
        "total": len(symbols),
        "summary": summary,
        "risks": grouped,
    }


def format_batch_result(result: dict[str, Any], top_n: int = 10) -> str:
    """
    格式化批量检查结果

    Args:
        result: 批量检查结果
        top_n: 每个风险等级显示数量

    Returns:
        格式化的字符串
    """
    lines = []
    lines.append("=" * 60)
    lines.append(f"风险扫描报告 - {result['date']}")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"检查股票: {result['total']} 只")
    lines.append("")

    # 汇总统计
    lines.append("【汇总统计】")
    summary = result["summary"]
    for level, count in summary.items():
        if count > 0:
            lines.append(f"  {level}: {count} 只")
    lines.append("")

    # 各风险等级详情
    for level in ["高风险", "中风险", "低风险", "正常"]:
        items = result["risks"][level]
        if not items:
            continue

        lines.append(f"【{level}】({len(items)} 只)")

        for i, item in enumerate(items[:top_n]):
            code = item.get("code", "?")
            name = item.get("name", "?")
            risks = item.get("risks", [])

            if risks:
                risk_desc = ", ".join([r.get("detail", "") for r in risks[:2]])
                lines.append(f"  {code} {name}: {risk_desc}")
            elif "error" in item:
                lines.append(f"  {code} {name}: 检查失败 ({item['error'][:30]}...)")
            else:
                lines.append(f"  {code} {name}: 无明显风险")

        if len(items) > top_n:
            lines.append(f"  ... 还有 {len(items) - top_n} 只")

        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


async def main():
    args = parse_args()
    check_date = args.date or datetime.now().strftime("%Y-%m-%d")

    # 获取股票列表
    symbols = get_stock_list(args)

    if symbols:
        # 批量检查
        result = await batch_check(symbols, args.date, args.days)

        # 打印格式化结果
        print(format_batch_result(result, args.top_n))

        # 保存到文件
        if args.output:
            output_path = get_output_path("risk_alert", "batch_risk_scan", check_date)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n结果已保存到: {output_path}")

    elif args.symbol:
        # 单股检查
        processor = RiskProcessor(symbol=args.symbol, date=args.date, days=args.days)
        result = await processor.check()

        # 打印结果
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 保存到文件
        if args.output:
            output_path = get_output_path("risk_alert", "risk_check", check_date)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n结果已保存到: {output_path}")

    else:
        print("请提供股票代码或使用批量检查参数：")
        print("  单股检查: risk_processor 000001")
        print("  批量检查: risk_processor --batch '000001,600000'")
        print("  文件读取: risk_processor --batch-file stocks.txt")
        print("  自选股:   risk_processor --watchlist")


if __name__ == "__main__":
    asyncio.run(main())
