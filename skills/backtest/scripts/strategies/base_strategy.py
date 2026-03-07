# -*- coding: utf-8 -*-
"""策略基类"""

import backtrader as bt


class BaseStrategy(bt.Strategy):
    """
    策略基类
    
    提供通用的策略参数和方法
    """
    
    # 策略参数（子类可覆盖）
    params = (
        ("printlog", True),  # 是否打印日志
    )
    
    def __init__(self):
        """初始化策略"""
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
    
    def notify_order(self, order):
        """
        订单状态通知
        
        Args:
            order: 订单对象
        """
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已提交/已接受，不做处理
            return
        
        # 检查订单是否完成
        if order.status in [order.Completed]:
            if order.isbuy():
                if self.p.printlog:
                    self.log(
                        f"买入执行: 价格={order.executed.price:.2f}, "
                        f"成本={order.executed.value:.2f}, "
                        f"手续费={order.executed.comm:.2f}"
                    )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                if self.p.printlog:
                    self.log(
                        f"卖出执行: 价格={order.executed.price:.2f}, "
                        f"成本={order.executed.value:.2f}, "
                        f"手续费={order.executed.comm:.2f}"
                    )
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            if self.p.printlog:
                self.log("订单取消/保证金不足/拒绝")
        
        # 清空订单
        self.order = None
    
    def notify_trade(self, trade):
        """
        交易通知
        
        Args:
            trade: 交易对象
        """
        if not trade.isclosed:
            return
        
        if self.p.printlog:
            self.log(f"交易盈亏: 毛利={trade.pnl:.2f}, 净利={trade.pnlcomm:.2f}")
    
    def log(self, txt, dt=None):
        """
        日志输出
        
        Args:
            txt: 日志内容
            dt: 日期时间
        """
        dt = dt or self.datas[0].datetime.date(0)
        if self.p.printlog:
            print(f"[{dt.isoformat()}] {txt}")
    
    def next(self):
        """策略逻辑（子类必须实现）"""
        raise NotImplementedError("子类必须实现 next() 方法")
