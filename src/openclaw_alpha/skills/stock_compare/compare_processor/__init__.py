# -*- coding: utf-8 -*-
"""对比处理器模块"""

from .compare_processor import (
    StockMetrics,
    StockScore,
    CompareResult,
    fetch_stock_metrics,
    compare_stocks,
    calculate_scores,
    format_compare_result,
)

__all__ = [
    "StockMetrics",
    "StockScore",
    "CompareResult",
    "fetch_stock_metrics",
    "compare_stocks",
    "calculate_scores",
    "format_compare_result",
]
