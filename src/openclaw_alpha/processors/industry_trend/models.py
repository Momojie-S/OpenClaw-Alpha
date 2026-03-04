# -*- coding: utf-8 -*-
"""产业趋势分析数据模型"""

from dataclasses import dataclass


@dataclass
class IndustryTrendProcessParams:
    """产业趋势加工参数"""

    top: int = 20
    """返回前 N 个板块"""

    sort_by: str = "change_pct"
    """排序字段：change_pct（涨跌幅）、amount（成交额）、turnover（换手率）"""


@dataclass
class BoardTrendItem:
    """板块趋势数据"""

    rank: int
    """排名"""

    board_code: str
    """板块代码"""

    board_name: str
    """板块名称"""

    change_pct: float
    """涨跌幅（%）"""

    turnover_rate: float
    """换手率（%）"""

    amount: float
    """成交额（亿元）"""

    data_source: str
    """数据来源（concept_board / sw_industry）"""


@dataclass
class IndustryTrendProcessResult:
    """产业趋势加工结果"""

    trade_date: str
    """交易日期"""

    concept_boards: list[BoardTrendItem]
    """概念板块数据"""

    sw_industries: list[BoardTrendItem]
    """申万行业数据"""
