# -*- coding: utf-8 -*-
"""财务指标数据模型"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FinancialData:
    """财务指标数据"""

    code: str  # 股票代码
    name: str  # 股票名称
    report_date: str  # 报告日期

    # 盈利能力
    roe: Optional[float] = None  # ROE(加权) %
    eps: Optional[float] = None  # 每股收益
    bps: Optional[float] = None  # 每股净资产
    net_profit_margin: Optional[float] = None  # 销售净利率 %
    gross_profit_margin: Optional[float] = None  # 销售毛利率 %

    # 成长能力
    revenue_growth: Optional[float] = None  # 营收同比增长 %
    profit_growth: Optional[float] = None  # 净利润同比增长 %

    # 财务健康
    debt_ratio: Optional[float] = None  # 资产负债率 %
    current_ratio: Optional[float] = None  # 流动比率
    quick_ratio: Optional[float] = None  # 速动比率
    cash_per_share: Optional[float] = None  # 每股经营现金流

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "code": self.code,
            "name": self.name,
            "report_date": self.report_date,
            "roe": self.roe,
            "eps": self.eps,
            "bps": self.bps,
            "net_profit_margin": self.net_profit_margin,
            "gross_profit_margin": self.gross_profit_margin,
            "revenue_growth": self.revenue_growth,
            "profit_growth": self.profit_growth,
            "debt_ratio": self.debt_ratio,
            "current_ratio": self.current_ratio,
            "quick_ratio": self.quick_ratio,
            "cash_per_share": self.cash_per_share,
        }
