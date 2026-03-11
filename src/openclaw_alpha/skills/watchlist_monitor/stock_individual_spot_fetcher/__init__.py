# -*- coding: utf-8 -*-
"""个股实时行情 Fetcher"""

from .stock_individual_spot_fetcher import (
    StockIndividualSpotFetcher,
    get_fetcher,
    fetch,
)

__all__ = ["StockIndividualSpotFetcher", "get_fetcher", "fetch"]
