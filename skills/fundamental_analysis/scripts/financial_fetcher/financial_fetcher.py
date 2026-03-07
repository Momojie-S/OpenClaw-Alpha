# -*- coding: utf-8 -*-
"""财务指标 Fetcher 入口类"""

from openclaw_alpha.core.fetcher import Fetcher
from .models import FinancialData


class FinancialFetcher(Fetcher):
    """财务指标获取器

    获取股票的财务分析指标，包括 ROE、EPS、资产负债率等。
    """

    name = "financial"

    async def fetch(self, code: str) -> FinancialData:
        """获取财务分析指标

        Args:
            code: 股票代码（如 "000001"）

        Returns:
            财务指标数据

        Raises:
            NoAvailableMethodError: 所有实现都不可用
        """
        return await super().fetch(code=code)
