# -*- coding: utf-8 -*-
"""概念板块成分股数据模型"""

from dataclasses import dataclass


@dataclass
class ConceptConsItem:
    """概念板块成分股数据项"""

    # 股票代码（6位数字）
    code: str
    # 股票名称
    name: str
    # 概念板块名称
    board_name: str
    # 最新价
    latest_price: float
    # 涨跌幅（%）
    change_pct: float
    # 涨跌额
    change_amount: float
    # 成交量（手）
    volume: float
    # 成交额（元）
    amount: float
    # 换手率（%）
    turnover_rate: float
    # 市盈率
    pe_ratio: float
    # 市净率
    pb_ratio: float

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "board_name": self.board_name,
            "latest_price": self.latest_price,
            "change_pct": self.change_pct,
            "change_amount": self.change_amount,
            "volume": self.volume,
            "amount": self.amount,
            "turnover_rate": self.turnover_rate,
            "pe_ratio": self.pe_ratio,
            "pb_ratio": self.pb_ratio,
        }
