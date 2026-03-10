# -*- coding: utf-8 -*-
"""估值数据 Fetcher 入口类"""

from typing import List

from openclaw_alpha.core.fetcher import Fetcher
from .models import ValuationData


class ValuationFetcher(Fetcher):
    """估值数据获取器

    获取股票的 PE、PB、市值等估值指标的历史数据。
    """

    name = "valuation"

    async def fetch(
        self, code: str, indicator: str, period: str = "近一年"
    ) -> List[ValuationData]:
        """获取估值数据

        Args:
            code: 股票代码（如 "000001"）
            indicator: 指标类型（"pe_ttm", "pe_static", "pb", "market_cap", "pcf"）
            period: 时间范围（默认 "近一年"）

        Returns:
            估值时间序列数据

        Raises:
            NoAvailableMethodError: 所有实现都不可用
        """
        return await super().fetch(code=code, indicator=indicator, period=period)
