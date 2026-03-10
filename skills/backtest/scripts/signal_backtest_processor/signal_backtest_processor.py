# -*- coding: utf-8 -*-
"""信号驱动回测 Processor"""

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from openclaw_alpha.core.processor_utils import get_output_path
from openclaw_alpha.core.signal_utils import load_signal_by_path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from skills.backtest.scripts.backtest_processor.backtest_processor import BacktestEngine
from skills.backtest.scripts.strategies.signal_strategy import SignalStrategy


class SignalBacktestProcessor:
    """信号驱动回测处理器"""

    def __init__(
        self,
        stock_code: str,
        signal_files: list[str],
        cash: float = 100000.0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        combine_mode: str = "single",
        printlog: bool = True,
    ):
        """初始化

        Args:
            stock_code: 股票代码
            signal_files: 信号文件路径列表
            cash: 初始资金
            start_date: 开始日期
            end_date: 结束日期
            combine_mode: 信号组合模式（single/and/or）
            printlog: 是否打印日志
        """
        self.stock_code = stock_code
        self.signal_files = signal_files
        self.cash = cash
        self.start_date = start_date
        self.end_date = end_date
        self.combine_mode = combine_mode
        self.printlog = printlog

    def _load_signals(self) -> list[dict]:
        """加载所有信号文件"""
        signals_list = []
        for path in self.signal_files:
            data = load_signal_by_path(path)
            if data:
                signals_list.append(data)
            else:
                if self.printlog:
                    print(f"警告: 信号文件不存在或无法加载: {path}")
        return signals_list

    def _combine_signals(self, signals_list: list[dict]) -> dict:
        """合并多个信号

        Args:
            signals_list: 信号文件数据列表

        Returns:
            合并后的信号数据
        """
        if len(signals_list) == 0:
            raise ValueError(
                "没有有效的信号文件。"
                "请检查信号文件路径是否正确，或先运行对应的 processor 生成信号文件"
            )

        if len(signals_list) == 1:
            return signals_list[0]

        # 按 combine_mode 合并
        if self.combine_mode == "single":
            # 使用第一个信号文件
            return signals_list[0]

        elif self.combine_mode == "and":
            # 所有信号一致才执行
            return self._combine_and(signals_list)

        elif self.combine_mode == "or":
            # 任一信号触发即执行
            return self._combine_or(signals_list)

        else:
            raise ValueError(
                f"参数 combine_mode '{self.combine_mode}' 不存在（收到 '{self.combine_mode}'）。"
                f"可用模式：single（单信号）、and（全部一致）、or（任一触发）"
            )

    def _combine_and(self, signals_list: list[dict]) -> dict:
        """AND 模式：所有信号一致才执行"""
        # 收集所有日期
        all_dates = set()
        for sig_data in signals_list:
            for sig in sig_data.get("signals", []):
                all_dates.add(sig["date"])

        # 检查每个日期
        combined_signals = []
        for date in sorted(all_dates):
            actions = []
            for sig_data in signals_list:
                for sig in sig_data.get("signals", []):
                    if sig["date"] == date:
                        actions.append(sig.get("action"))
                        break

            # 所有信号一致
            if actions and all(a == actions[0] for a in actions):
                combined_signals.append({
                    "date": date,
                    "action": actions[0],
                    "score": 1,
                    "reason": f"AND 组合 ({len(actions)} 个信号)",
                })

        # 构建合并后的信号数据
        return {
            "signal_id": f"combined_and_{len(signals_list)}",
            "signal_type": "combined",
            "stock_code": self.stock_code,
            "generated_at": datetime.now().isoformat(),
            "params": {"mode": "and", "sources": [s.get("signal_id") for s in signals_list]},
            "signals": combined_signals,
            "summary": {
                "total_signals": len(combined_signals),
                "buy_signals": sum(1 for s in combined_signals if s["action"] == "buy"),
                "sell_signals": sum(1 for s in combined_signals if s["action"] == "sell"),
            }
        }

    def _combine_or(self, signals_list: list[dict]) -> dict:
        """OR 模式：任一信号触发即执行"""
        # 收集所有信号
        signal_map = {}
        for sig_data in signals_list:
            for sig in sig_data.get("signals", []):
                date = sig["date"]
                action = sig.get("action")
                if date not in signal_map:
                    signal_map[date] = {"buy": 0, "sell": 0}
                signal_map[date][action] = signal_map[date].get(action, 0) + 1

        # 选择票数多的动作
        combined_signals = []
        for date in sorted(signal_map.keys()):
            votes = signal_map[date]
            if votes["buy"] > votes["sell"]:
                combined_signals.append({
                    "date": date,
                    "action": "buy",
                    "score": 1,
                    "reason": f"OR 组合 (买入 {votes['buy']} vs 卖出 {votes['sell']})",
                })
            elif votes["sell"] > votes["buy"]:
                combined_signals.append({
                    "date": date,
                    "action": "sell",
                    "score": -1,
                    "reason": f"OR 组合 (卖出 {votes['sell']} vs 买入 {votes['buy']})",
                })

        # 构建合并后的信号数据
        return {
            "signal_id": f"combined_or_{len(signals_list)}",
            "signal_type": "combined",
            "stock_code": self.stock_code,
            "generated_at": datetime.now().isoformat(),
            "params": {"mode": "or", "sources": [s.get("signal_id") for s in signals_list]},
            "signals": combined_signals,
            "summary": {
                "total_signals": len(combined_signals),
                "buy_signals": sum(1 for s in combined_signals if s["action"] == "buy"),
                "sell_signals": sum(1 for s in combined_signals if s["action"] == "sell"),
            }
        }

    async def run(self) -> dict:
        """运行回测

        Returns:
            回测结果
        """
        # 加载信号
        signals_list = self._load_signals()
        if not signals_list:
            raise ValueError(
                "没有有效的信号文件。"
                "请检查信号文件路径是否正确，或先运行对应的 processor 生成信号文件"
            )

        if self.printlog:
            print(f"加载了 {len(signals_list)} 个信号文件")
            for sig in signals_list:
                print(f"  - {sig.get('signal_id')}: {sig.get('summary', {}).get('total_signals', 0)} 个信号")

        # 合并信号
        combined_signal = self._combine_signals(signals_list)

        if self.printlog:
            print(f"合并后信号: {combined_signal.get('summary', {}).get('total_signals', 0)} 个")

        # 保存合并后的信号文件
        merged_path = get_output_path("backtest", "merged_signal", ext="json")
        merged_path.parent.mkdir(parents=True, exist_ok=True)
        with open(merged_path, "w", encoding="utf-8") as f:
            json.dump(combined_signal, f, ensure_ascii=False, indent=2)

        if self.printlog:
            print(f"合并信号保存到: {merged_path}")

        # 从信号文件推断日期范围
        if not self.start_date or not self.end_date:
            date_range = combined_signal.get("summary", {}).get("date_range", {})
            self.start_date = self.start_date or date_range.get("start")
            self.end_date = self.end_date or date_range.get("end")

        # 创建回测引擎
        engine = BacktestEngine(
            strategy=SignalStrategy,
            stock_code=self.stock_code,
            start_date=self.start_date,
            end_date=self.end_date,
            cash=self.cash,
            printlog=self.printlog,
            strategy_params={"signal_file": str(merged_path)},
        )

        # 运行回测
        result = await engine.run()

        # 添加信号信息
        result["signal_info"] = {
            "files": [Path(p).name for p in self.signal_files],
            "combine_mode": self.combine_mode,
            "signal_count": combined_signal.get("summary", {}).get("total_signals", 0),
        }

        return result

    def print_result(self, result: dict):
        """打印精简结果"""
        print(f"\n信号驱动回测 - {result['stock_code']}")
        print("=" * 50)
        print(f"策略: {result['strategy']}")
        print(f"信号文件: {', '.join(result.get('signal_info', {}).get('files', []))}")
        print(f"组合模式: {result.get('signal_info', {}).get('combine_mode', 'single')}")
        print(f"信号数量: {result.get('signal_info', {}).get('signal_count', 0)}")
        print()

        # 交易统计
        perf = result.get("performance", {})
        print("【交易统计】")
        print(f"初始资金: {result['initial_cash']:,.2f}")
        print(f"最终价值: {result['final_value']:,.2f}")
        print(f"总收益率: {perf.get('total_return', 0):.2f}%")
        print(f"年化收益率: {perf.get('annual_return', 0):.2f}%")
        print()

        # 风险指标
        print("【风险指标】")
        print(f"夏普比率: {perf.get('sharpe_ratio', 0):.2f}")
        print(f"最大回撤: {perf.get('max_drawdown', 0):.2f}%")
        print()

        # 交易记录
        trades = result.get("trades", [])
        if trades:
            print(f"【交易记录】共 {len(trades)} 笔")
            for trade in trades[:10]:  # 只显示前 10 笔
                print(f"  {trade['type']}: {trade['date']} @ {trade['price']:.2f}")
            if len(trades) > 10:
                print(f"  ... 还有 {len(trades) - 10} 笔")


def parse_args():
    parser = argparse.ArgumentParser(description="信号驱动回测")
    parser.add_argument("--stock", required=True, help="股票代码")
    parser.add_argument(
        "--signals",
        required=True,
        help="信号文件路径（多个用逗号分隔）",
    )
    parser.add_argument("--cash", type=float, default=100000.0, help="初始资金")
    parser.add_argument("--start-date", help="开始日期（YYYY-MM-DD）")
    parser.add_argument("--end-date", help="结束日期（YYYY-MM-DD）")
    parser.add_argument(
        "--combine",
        choices=["single", "and", "or"],
        default="single",
        help="信号组合模式",
    )
    parser.add_argument("--quiet", action="store_true", help="安静模式")
    parser.add_argument("--output", help="输出文件路径")

    return parser.parse_args()


def main():
    args = parse_args()

    # 解析信号文件
    signal_files = [p.strip() for p in args.signals.split(",")]

    # 创建处理器
    processor = SignalBacktestProcessor(
        stock_code=args.stock,
        signal_files=signal_files,
        cash=args.cash,
        start_date=args.start_date,
        end_date=args.end_date,
        combine_mode=args.combine,
        printlog=not args.quiet,
    )

    # 运行回测
    result = asyncio.run(processor.run())

    # 打印结果
    if not args.quiet:
        processor.print_result(result)

    # 保存结果
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = get_output_path(
            "backtest",
            f"signal_backtest_{args.stock}",
            datetime.now().strftime("%Y-%m-%d"),
            ext="json",
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    if not args.quiet:
        print(f"\n完整结果已保存到: {output_path}")


if __name__ == "__main__":
    main()
