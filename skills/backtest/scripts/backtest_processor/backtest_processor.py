# -*- coding: utf-8 -*-
"""回测主流程"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Type

import backtrader as bt

from openclaw_alpha.core.processor_utils import get_output_path
from .data_adapter import DataAdapter
from ..strategies import MACrossStrategy
from ..strategies.base_strategy import BaseStrategy


# 策略注册表
STRATEGY_REGISTRY = {
    "ma_cross": MACrossStrategy,
}


class BacktestEngine:
    """
    回测引擎
    
    负责运行回测并输出结果
    """
    
    def __init__(
        self,
        strategy: Type[BaseStrategy],
        stock_code: str,
        start_date: str,
        end_date: str,
        cash: float = 100000.0,
        commission: float = 0.0003,
        stamp_duty: float = 0.001,
        printlog: bool = True,
        strategy_params: Optional[dict] = None,
    ):
        """
        初始化回测引擎
        
        Args:
            strategy: 策略类
            stock_code: 股票代码
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            cash: 初始资金（默认 10 万）
            commission: 佣金率（默认 0.03%）
            stamp_duty: 印花税率（默认 0.1%，仅卖出）
            printlog: 是否打印日志
            strategy_params: 策略参数
        """
        self.strategy = strategy
        self.stock_code = stock_code
        self.start_date = start_date
        self.end_date = end_date
        self.cash = cash
        self.commission = commission
        self.stamp_duty = stamp_duty
        self.printlog = printlog
        self.strategy_params = strategy_params or {}
        
        # 回测结果
        self.results = None
        self.final_value = 0.0
        self.trade_records = []
        self.performance = {}
    
    def run(self) -> dict:
        """
        运行回测
        
        Returns:
            回测结果字典
        """
        # 创建 Cerebro 引擎
        cerebro = bt.Cerebro()
        
        # 设置初始资金
        cerebro.broker.setcash(self.cash)
        
        # 设置手续费（A股：佣金双向收取，印花税仅卖出收取）
        # backtrader 默认按百分比计算佣金
        cerebro.broker.setcommission(commission=self.commission)
        
        # 获取数据（同步调用）
        adapter = DataAdapter()
        df = adapter.fetch_stock_data(
            self.stock_code,
            self.start_date,
            self.end_date
        )
        data = adapter.transform_to_backtrader(df, self.stock_code)
        
        # 添加数据
        cerebro.adddata(data)
        
        # 添加策略
        strategy_params = {"printlog": self.printlog}
        strategy_params.update(self.strategy_params)
        cerebro.addstrategy(self.strategy, **strategy_params)
        
        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
        
        # 打印初始资金
        if self.printlog:
            print(f"\n{'='*60}")
            print(f"回测配置")
            print(f"{'='*60}")
            print(f"股票代码: {self.stock_code}")
            print(f"回测区间: {self.start_date} ~ {self.end_date}")
            print(f"初始资金: {self.cash:,.2f}")
            print(f"策略: {self.strategy.__name__}")
            print(f"策略参数: {self.strategy_params}")
            print(f"{'='*60}\n")
        
        # 运行回测
        self.results = cerebro.run()
        
        # 获取最终资金
        self.final_value = cerebro.broker.getvalue()
        
        # 提取分析结果
        self._extract_results()
        
        return self.get_summary()
    
    def _extract_results(self):
        """提取回测结果"""
        if not self.results:
            return
        
        strat = self.results[0]
        
        # 收益率分析
        returns = strat.analyzers.returns.get_analysis()
        sharpe = strat.analyzers.sharpe.get_analysis()
        drawdown = strat.analyzers.drawdown.get_analysis()
        trades = strat.analyzers.trades.get_analysis()
        
        # 计算总收益率
        total_return = (self.final_value - self.cash) / self.cash * 100
        
        # 提取关键指标
        self.performance = {
            "total_return": round(total_return, 2),
            "annual_return": round(returns.get("rnorm100", 0), 2),
            "sharpe_ratio": round(sharpe.get("sharperatio", 0) or 0, 2),
            "max_drawdown": round(drawdown.get("max", {}).get("drawdown", 0), 2),
            "total_trades": trades.get("total", {}).get("total", 0),
            "won_trades": trades.get("won", {}).get("total", 0),
            "lost_trades": trades.get("lost", {}).get("total", 0),
        }
        
        # 计算胜率
        total = self.performance["total_trades"]
        won = self.performance["won_trades"]
        self.performance["win_rate"] = round(won / total * 100, 2) if total > 0 else 0.0
    
    def get_summary(self) -> dict:
        """
        获取回测摘要
        
        Returns:
            回测结果摘要
        """
        return {
            "stock_code": self.stock_code,
            "strategy": self.strategy.__name__,
            "strategy_params": self.strategy_params,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_cash": self.cash,
            "final_value": round(self.final_value, 2),
            "performance": self.performance,
        }
    
    def print_summary(self):
        """打印回测摘要"""
        print(f"\n{'='*60}")
        print(f"回测结果")
        print(f"{'='*60}")
        print(f"最终资金: {self.final_value:,.2f}")
        print(f"总收益率: {self.performance['total_return']:.2f}%")
        print(f"年化收益率: {self.performance['annual_return']:.2f}%")
        print(f"夏普比率: {self.performance['sharpe_ratio']:.2f}")
        print(f"最大回撤: {self.performance['max_drawdown']:.2f}%")
        print(f"总交易次数: {self.performance['total_trades']}")
        print(f"胜率: {self.performance['win_rate']:.2f}%")
        print(f"{'='*60}\n")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="策略回测")
    parser.add_argument(
        "--stock",
        required=True,
        help="股票代码（如 000001）"
    )
    parser.add_argument(
        "--strategy",
        default="ma_cross",
        choices=list(STRATEGY_REGISTRY.keys()),
        help="策略名称（默认: ma_cross）"
    )
    parser.add_argument(
        "--start-date",
        default=(datetime.now().replace(year=datetime.now().year - 1)).strftime("%Y-%m-%d"),
        help="开始日期（默认: 一年前）"
    )
    parser.add_argument(
        "--end-date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="结束日期（默认: 今天）"
    )
    parser.add_argument(
        "--cash",
        type=float,
        default=100000.0,
        help="初始资金（默认: 100000）"
    )
    parser.add_argument(
        "--fast-period",
        type=int,
        default=5,
        help="快速均线周期（仅 ma_cross 策略）"
    )
    parser.add_argument(
        "--slow-period",
        type=int,
        default=20,
        help="慢速均线周期（仅 ma_cross 策略）"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="安静模式（不打印详细日志）"
    )
    parser.add_argument(
        "--output",
        help="输出文件路径（默认自动生成）"
    )
    return parser.parse_args()


def backtest(
    stock: str,
    strategy: str = "ma_cross",
    start_date: str = None,
    end_date: str = None,
    cash: float = 100000.0,
    fast_period: int = 5,
    slow_period: int = 20,
    quiet: bool = False,
    output: str = None,
) -> dict:
    """
    运行回测
    
    Args:
        stock: 股票代码
        strategy: 策略名称
        start_date: 开始日期
        end_date: 结束日期
        cash: 初始资金
        fast_period: 快速均线周期
        slow_period: 慢速均线周期
        quiet: 是否安静模式
        output: 输出文件路径
    
    Returns:
        回测结果
    """
    # 设置默认日期
    if not start_date:
        start_date = (datetime.now().replace(year=datetime.now().year - 1)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # 获取策略类
    strategy_class = STRATEGY_REGISTRY.get(strategy)
    if not strategy_class:
        raise ValueError(f"未知策略: {strategy}")
    
    # 策略参数
    strategy_params = {}
    if strategy == "ma_cross":
        strategy_params = {
            "fast_period": fast_period,
            "slow_period": slow_period,
        }
    
    # 创建引擎并运行
    engine = BacktestEngine(
        strategy=strategy_class,
        stock_code=stock,
        start_date=start_date,
        end_date=end_date,
        cash=cash,
        printlog=not quiet,
        strategy_params=strategy_params,
    )
    
    result = engine.run()
    
    # 打印摘要
    if not quiet:
        engine.print_summary()
    
    # 保存结果
    if output:
        output_path = Path(output)
    else:
        output_path = get_output_path("backtest", "backtest", ext="json")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    if not quiet:
        print(f"完整结果已保存到: {output_path}")
    
    return result


def main():
    """命令行入口"""
    args = parse_args()
    
    result = backtest(
        stock=args.stock,
        strategy=args.strategy,
        start_date=args.start_date,
        end_date=args.end_date,
        cash=args.cash,
        fast_period=args.fast_period,
        slow_period=args.slow_period,
        quiet=args.quiet,
        output=args.output,
    )
    
    # 输出精简结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
