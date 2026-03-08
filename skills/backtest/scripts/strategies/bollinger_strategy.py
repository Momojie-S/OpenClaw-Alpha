# -*- coding: utf-8 -*-
"""布林带策略"""

import backtrader as bt

from .base_strategy import BaseStrategy


class BollingerBandsStrategy(BaseStrategy):
    """
    布林带突破策略
    
    买入信号：价格从下往上穿越下轨（反弹）
    卖出信号：价格从上往下穿越上轨（回调）
    
    参数：
        period: 布林带周期（默认 20）
        devfactor: 标准差倍数（默认 2.0）
        printlog: 是否打印日志
    """
    
    params = (
        ("period", 20),
        ("devfactor", 2.0),
        ("printlog", True),
    )
    
    def __init__(self):
        """初始化策略"""
        super().__init__()
        
        # 计算布林带
        self.boll = bt.indicators.BollingerBands(
            self.datas[0].close,
            period=self.p.period,
            devfactor=self.p.devfactor
        )
        
        # 布林带上轨、中轨、下轨
        self.top = self.boll.top
        self.mid = self.boll.mid
        self.bot = self.boll.bot
        
        # 价格穿越信号
        self.cross_over_top = bt.indicators.CrossUp(self.datas[0].close, self.bot)
        self.cross_under_top = bt.indicators.CrossDown(self.datas[0].close, self.top)
    
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
            if self.cross_over_top:
                # 价格上穿下轨，反弹信号
                if self.p.printlog:
                    self.log(
                        f"买入信号: 价格={self.dataclose[0]:.2f}, "
                        f"下轨={self.bot[0]:.2f}"
                    )
                # 全仓买入
                self.order = self.buy()
        else:
            # 有持仓，检查卖出信号
            if self.cross_under_top:
                # 价格下穿上轨，回调信号
                if self.p.printlog:
                    self.log(
                        f"卖出信号: 价格={self.dataclose[0]:.2f}, "
                        f"上轨={self.top[0]:.2f}"
                    )
                # 清仓卖出
                self.order = self.sell()
