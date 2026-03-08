# -*- coding: utf-8 -*-
"""RSI 超买超卖策略"""

import backtrader as bt

from .base_strategy import BaseStrategy


class RSIStrategy(BaseStrategy):
    """
    RSI 超买超卖策略
    
    买入信号：RSI 从下往上穿越超卖线（默认 30）
    卖出信号：RSI 从上往下穿越超买线（默认 70）
    
    参数：
        rsi_period: RSI 计算周期（默认 14）
        rsi_upper: 超买阈值（默认 70）
        rsi_lower: 超卖阈值（默认 30）
        printlog: 是否打印日志
    """
    
    params = (
        ("rsi_period", 14),
        ("rsi_upper", 70),
        ("rsi_lower", 30),
        ("printlog", True),
    )
    
    def __init__(self):
        """初始化策略"""
        super().__init__()
        
        # 计算 RSI 指标
        self.rsi = bt.indicators.RSI(
            self.datas[0].close,
            period=self.p.rsi_period
        )
        
        # RSI 穿越信号
        self.cross_over_upper = bt.indicators.CrossUp(self.rsi, self.p.rsi_upper)
        self.cross_under_lower = bt.indicators.CrossDown(self.rsi, self.p.rsi_lower)
    
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
            if self.cross_under_lower:
                # RSI 下穿超卖线，进入超卖区域（买入机会）
                if self.p.printlog:
                    self.log(f"买入信号: RSI={self.rsi[0]:.2f} (超卖)")
                # 全仓买入
                self.order = self.buy()
        else:
            # 有持仓，检查卖出信号
            if self.cross_over_upper:
                # RSI 上穿超买线，进入超买区域（卖出信号）
                if self.p.printlog:
                    self.log(f"卖出信号: RSI={self.rsi[0]:.2f} (超买)")
                # 清仓卖出
                self.order = self.sell()
