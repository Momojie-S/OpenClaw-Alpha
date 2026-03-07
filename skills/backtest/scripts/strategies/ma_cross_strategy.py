# -*- coding: utf-8 -*-
"""均线交叉策略"""

import backtrader as bt

from .base_strategy import BaseStrategy


class MACrossStrategy(BaseStrategy):
    """
    均线交叉策略
    
    买入信号：快速均线上穿慢速均线（金叉）
    卖出信号：快速均线下穿慢速均线（死叉）
    
    参数：
        fast_period: 快速均线周期（默认 5）
        slow_period: 慢速均线周期（默认 20）
        printlog: 是否打印日志
    """
    
    params = (
        ("fast_period", 5),
        ("slow_period", 20),
        ("printlog", True),
    )
    
    def __init__(self):
        """初始化策略"""
        super().__init__()
        
        # 计算均线
        self.fast_ma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close,
            period=self.p.fast_period
        )
        self.slow_ma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close,
            period=self.p.slow_period
        )
        
        # 均线交叉信号
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
    
    def next(self):
        """
        策略逻辑
        
        每个交易日执行一次
        """
        # 如果有待执行的订单，不操作
        if self.order:
            return
        
        # 检查是否持仓
        if not self.position:
            # 无持仓，检查买入信号
            if self.crossover > 0:
                # 金叉，买入
                if self.p.printlog:
                    self.log(
                        f"买入信号: 快线={self.fast_ma[0]:.2f}, "
                        f"慢线={self.slow_ma[0]:.2f}"
                    )
                # 全仓买入
                self.order = self.buy()
        else:
            # 有持仓，检查卖出信号
            if self.crossover < 0:
                # 死叉，卖出
                if self.p.printlog:
                    self.log(
                        f"卖出信号: 快线={self.fast_ma[0]:.2f}, "
                        f"慢线={self.slow_ma[0]:.2f}"
                    )
                # 清仓卖出
                self.order = self.sell()
