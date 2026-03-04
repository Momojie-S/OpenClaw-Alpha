# -*- coding: utf-8 -*-
"""申万行业数据模型"""

from dataclasses import dataclass


@dataclass
class SwIndustryFetchParams:
    """申万行业获取参数"""

    trade_date: str | None = None
    """交易日期 (YYYYMMDD)，默认为当日"""

    level: str = "L3"
    """行业层级 (L1/L2/L3)"""

    top: int = 50
    """返回前 N 个行业"""

    sort_by: str = "change_pct"
    """排序字段：change_pct（涨跌幅）、amount（成交额）、turnover_rate（换手率）"""


@dataclass
class SwIndustryItem:
    """申万行业单项数据"""

    rank: int
    """排名"""

    board_code: str
    """行业代码"""

    board_name: str
    """行业名称"""

    change_pct: float
    """涨跌幅（%）"""

    close: float
    """收盘价"""

    volume: float
    """成交量（万手）"""

    amount: float
    """成交额（亿元）"""

    turnover_rate: float
    """换手率（%）"""

    float_mv: float
    """流通市值（亿）"""

    total_mv: float
    """总市值（亿）"""

    pe: float
    """市盈率"""

    pb: float
    """市净率"""


@dataclass
class SwIndustryFetchResult:
    """申万行业获取结果"""

    trade_date: str
    """交易日期（YYYYMMDD）"""

    level: str
    """行业层级"""

    data_source: str
    """数据源名称"""

    items: list[SwIndustryItem]
    """行业数据列表"""
