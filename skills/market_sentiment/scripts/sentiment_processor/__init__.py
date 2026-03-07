# -*- coding: utf-8 -*-
"""市场情绪分析处理器"""

from .sentiment_processor import MarketSentimentProcessor


def process(date: str = None) -> dict:
    """
    分析市场情绪

    Args:
        date: 交易日期，格式 YYYY-MM-DD，默认最近

    Returns:
        市场情绪分析结果
    """
    import asyncio

    processor = MarketSentimentProcessor()
    return asyncio.run(processor.process(date=date))
