# -*- coding: utf-8 -*-
"""交易记录分析器"""

import backtrader as bt


class TradeRecorder(bt.Analyzer):
    """
    交易记录分析器
    
    记录所有交易的详细信息，用于输出到文件
    """
    
    def __init__(self):
        """初始化分析器"""
        self.trades = []
        self.orders = []
    
    def notify_order(self, order):
        """
        订单通知
        
        Args:
            order: 订单对象
        """
        if order.status in [order.Completed]:
            order_info = {
                "date": self.strategy.datas[0].datetime.date(0).isoformat(),
                "type": "BUY" if order.isbuy() else "SELL",
                "price": order.executed.price,
                "size": order.executed.size,
                "value": order.executed.value,
                "commission": order.executed.comm,
            }
            self.orders.append(order_info)
    
    def notify_trade(self, trade):
        """
        交易通知
        
        Args:
            trade: 交易对象
        """
        if trade.isclosed:
            trade_info = {
                "open_date": bt.num2date(trade.dtopen).date().isoformat(),
                "close_date": bt.num2date(trade.dtclose).date().isoformat(),
                "open_price": trade.price,
                "close_price": trade.price + trade.pnl / trade.size,
                "size": trade.size,
                "pnl": trade.pnl,
                "pnl_comm": trade.pnlcomm,
                "commission": trade.commission,
            }
            self.trades.append(trade_info)
    
    def get_analysis(self):
        """
        获取分析结果
        
        Returns:
            包含订单和交易记录的字典
        """
        return {
            "orders": self.orders,
            "trades": self.trades,
        }
