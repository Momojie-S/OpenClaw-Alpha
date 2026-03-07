# -*- coding: utf-8 -*-
"""指数行情获取器入口"""

from typing import Optional

from openclaw_alpha.core.fetcher import Fetcher

from .akshare import IndexFetcherAkshare


class IndexFetcher(Fetcher):
    """指数行情获取器入口"""

    name = "index"

    def __init__(self):
        super().__init__()
        # 注册 AKShare 实现
        self.register(IndexFetcherAkshare())

    async def fetch(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[dict]:
        """
        获取指数历史行情数据。

        Args:
            symbol: 指数代码（如 sh000001）
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）

        Returns:
            行情数据列表
        """
        return await self._fetch({
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
        })
