# -*- coding: utf-8 -*-
"""数据源实现模块"""

from openclaw_alpha.core.registry import DataSourceRegistry
from openclaw_alpha.data_sources.akshare import AkshareDataSource
from openclaw_alpha.data_sources.tushare import TushareDataSource

# 注册数据源
registry = DataSourceRegistry.get_instance()
registry.register(TushareDataSource)
registry.register(AkshareDataSource)

__all__ = [
    "TushareDataSource",
    "AkshareDataSource",
    "registry",
]
