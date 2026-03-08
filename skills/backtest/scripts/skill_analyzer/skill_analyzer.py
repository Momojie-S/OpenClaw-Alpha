# -*- coding: utf-8 -*-
"""Skill 回测验证与改进分析"""

import argparse
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from openclaw_alpha.core.signal_utils import list_signals
from skills.technical_indicators.scripts.indicator_processor.indicator_processor import IndicatorProcessor


class SkillBacktestAnalyzer:
    """Skill 回测验证分析器

    定期对已有 skill 进行回测验证，分析结果并记录改进建议。
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """初始化

        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir or Path(".openclaw_alpha/analysis")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 测试股票池（代表性股票）
        self.test_stocks = [
            "000001",  # 平安银行 - 金融
            "600519",  # 贵州茅台 - 消费
            "000858",  # 五粮液 - 消费
            "002475",  # 立讯精密 - 科技
            "300750",  # 宁德时代 - 新能源
        ]

    async def analyze_technical_indicators(self) -> dict:
        """分析技术指标 skill

        Returns:
            分析结果
        """
        results = {
            "skill": "technical_indicators",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "stocks": {},
            "summary": {},
            "recommendations": [],
        }

        total_signals = 0
        buy_count = 0
        sell_count = 0

        for stock in self.test_stocks:
            try:
                # 生成信号
                processor = IndicatorProcessor(
                    symbol=stock,
                    days=120,
                    signal_only=True,
                )
                signal_paths = await processor.extract_signals()

                # 统计信号
                stock_signals = {}
                for signal_type, path in signal_paths.items():
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        signals = data.get("signals", [])
                        stock_signals[signal_type] = {
                            "total": len(signals),
                            "buy": sum(1 for s in signals if s["action"] == "buy"),
                            "sell": sum(1 for s in signals if s["action"] == "sell"),
                        }
                        total_signals += len(signals)
                        buy_count += stock_signals[signal_type]["buy"]
                        sell_count += stock_signals[signal_type]["sell"]

                results["stocks"][stock] = {
                    "signals": stock_signals,
                    "status": "success",
                }

            except Exception as e:
                results["stocks"][stock] = {
                    "status": "error",
                    "error": str(e),
                }

        # 汇总
        results["summary"] = {
            "total_stocks": len(self.test_stocks),
            "success_stocks": sum(1 for s in results["stocks"].values() if s.get("status") == "success"),
            "total_signals": total_signals,
            "buy_signals": buy_count,
            "sell_signals": sell_count,
            "buy_sell_ratio": round(buy_count / sell_count, 2) if sell_count > 0 else 0,
        }

        # 生成改进建议
        results["recommendations"] = self._generate_recommendations(results)

        return results

    def _generate_recommendations(self, results: dict) -> list[dict]:
        """生成改进建议

        Args:
            results: 分析结果

        Returns:
            改进建议列表
        """
        recommendations = []

        summary = results["summary"]

        # 买卖比例分析
        buy_sell_ratio = summary.get("buy_sell_ratio", 0)
        if buy_sell_ratio > 1.5:
            recommendations.append({
                "type": "signal_balance",
                "priority": "medium",
                "issue": f"买入信号过多（比例 {buy_sell_ratio}），可能导致虚假信号",
                "suggestion": "考虑调整阈值，减少买入信号触发条件",
            })
        elif buy_sell_ratio < 0.67:
            recommendations.append({
                "type": "signal_balance",
                "priority": "medium",
                "issue": f"卖出信号过多（比例 {buy_sell_ratio}），可能错过上涨机会",
                "suggestion": "考虑放宽卖出条件或增加持仓周期",
            })

        # 信号数量分析
        signals_per_stock = summary["total_signals"] / max(summary["success_stocks"], 1)
        if signals_per_stock > 20:
            recommendations.append({
                "type": "signal_frequency",
                "priority": "high",
                "issue": f"信号过于频繁（平均 {signals_per_stock:.1f} 个/股），可能过度交易",
                "suggestion": "增加信号过滤条件，减少交易频率",
            })
        elif signals_per_stock < 3:
            recommendations.append({
                "type": "signal_frequency",
                "priority": "low",
                "issue": f"信号过于稀少（平均 {signals_per_stock:.1f} 个/股），可能错过机会",
                "suggestion": "考虑降低阈值或增加信号类型",
            })

        # 错误分析
        error_stocks = [s for s, r in results["stocks"].items() if r.get("status") == "error"]
        if error_stocks:
            recommendations.append({
                "type": "data_quality",
                "priority": "high",
                "issue": f"部分股票数据获取失败：{', '.join(error_stocks)}",
                "suggestion": "检查数据源可用性，考虑添加备用数据源",
            })

        return recommendations

    def save_report(self, results: dict, skill_name: str):
        """保存分析报告

        Args:
            results: 分析结果
            skill_name: Skill 名称
        """
        date = results["date"]
        report_path = self.output_dir / f"{skill_name}_analysis_{date}.json"
        report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"分析报告已保存: {report_path}")

    def print_summary(self, results: dict):
        """打印摘要

        Args:
            results: 分析结果
        """
        print(f"\n{'='*60}")
        print(f"Skill 回测验证报告 - {results['skill']}")
        print(f"{'='*60}")
        print(f"分析日期: {results['date']}")
        print()

        # 汇总
        summary = results["summary"]
        print("【汇总统计】")
        print(f"测试股票: {summary['success_stocks']}/{summary['total_stocks']}")
        print(f"总信号数: {summary['total_signals']}")
        print(f"买入信号: {summary['buy_signals']}")
        print(f"卖出信号: {summary['sell_signals']}")
        print(f"买卖比例: {summary['buy_sell_ratio']}")
        print()

        # 各股票详情
        print("【各股票详情】")
        for stock, data in results["stocks"].items():
            if data.get("status") == "success":
                signals = data.get("signals", {})
                signal_str = ", ".join([f"{k}: {v['total']}" for k, v in signals.items()])
                print(f"  {stock}: {signal_str}")
            else:
                print(f"  {stock}: 错误 - {data.get('error', '未知')}")
        print()

        # 改进建议
        if results["recommendations"]:
            print("【改进建议】")
            for i, rec in enumerate(results["recommendations"], 1):
                print(f"{i}. [{rec['priority'].upper()}] {rec['type']}")
                print(f"   问题: {rec['issue']}")
                print(f"   建议: {rec['suggestion']}")
                print()


async def analyze_and_report():
    """执行分析并生成报告"""
    analyzer = SkillBacktestAnalyzer()

    # 分析技术指标
    print("正在分析 technical_indicators skill...")
    results = await analyzer.analyze_technical_indicators()

    # 打印摘要
    analyzer.print_summary(results)

    # 保存报告
    analyzer.save_report(results, "technical_indicators")

    return results


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="Skill 回测验证与改进分析")
    parser.add_argument("--skill", default="technical_indicators", help="要分析的 skill")
    parser.add_argument("--stocks", help="测试股票（逗号分隔）")
    args = parser.parse_args()

    asyncio.run(analyze_and_report())


if __name__ == "__main__":
    main()
