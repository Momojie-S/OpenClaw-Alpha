# -*- coding: utf-8 -*-
"""涨停追踪 Fetcher"""

from .limit_up_fetcher import fetch, LimitUpFetcher
from .models import LimitUpItem, LimitUpResult, LimitUpType

__all__ = ["fetch", "LimitUpFetcher", "LimitUpItem", "LimitUpResult", "LimitUpType"]
