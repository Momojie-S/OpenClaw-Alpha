# -*- coding: utf-8 -*-
"""概念板块数据模型"""

from dataclasses import dataclass


@dataclass
class ConceptBoardFetchParams:
    """概念板块获取参数"""

    top: int = 20
    """返回前 N 个板块"""

    sort_by: str = "change_pct"
    """排序字段：change_pct（涨跌幅）、amount（成交额）、volume（成交量）、turnover（换手率）"""


@dataclass
class ConceptBoardItem:
    """概念板块单项数据"""

    rank: int
    """排名"""

    board_code: str
    """板块代码"""

    board_name: str
    """板块名称"""

    price: float
    """最新价"""

    change_pct: float
    """涨跌幅（%）"""

    change: float
    """涨跌额"""

    volume: float
    """成交量（手）"""

    amount: float
    """成交额（元）"""

    turnover_rate: float
    """换手率（%）"""

    up_count: int
    """上涨家数"""

    down_count: int
    """下跌家数"""

    leader_name: str
    """领涨股票名称"""

    leader_change: float
    """领涨股票涨跌幅（%）"""

    total_mv: float
    """总市值（元）"""


@dataclass
class ConceptBoardFetchResult:
    """概念板块获取结果"""

    trade_date: str
    """交易日期（YYYY-MM-DD）"""

    data_source: str
    """数据源名称"""

    items: list[ConceptBoardItem]
    """板块数据列表"""
