# -*- coding: utf-8 -*-
"""概念板块成分股数据获取器"""

from typing import Literal

from openclaw_alpha.core.fetcher import Fetcher
from .models import ConceptConsItem


class ConceptConsFetcher(Fetcher):
    """概念板块成分股数据获取器

    获取概念板块的成分股列表，包括股票代码、名称、行情数据等。

    注意：Tushare 没有提供概念板块成分股接口，
    因此只使用 AKShare 作为数据源。
    """

    name = "concept_cons"

    def __init__(self):
        """初始化概念板块成分股 Fetcher"""
        super().__init__()

        # 只使用 AKShare
        from .akshare import ConceptConsFetcherAkshare

        self.register(ConceptConsFetcherAkshare(), priority=10)


async def fetch(
    board_name: str,
) -> list[ConceptConsItem]:
    """获取概念板块成分股

    Args:
        board_name: 概念板块名称（如"人工智能"）

    Returns:
        概念板块成分股列表

    Raises:
        NoAvailableMethodError: 所有数据源都不可用
        ValueError: 板块名称不存在
    """
    fetcher = ConceptConsFetcher()
    result = await fetcher.fetch(board_name=board_name)
    return result
