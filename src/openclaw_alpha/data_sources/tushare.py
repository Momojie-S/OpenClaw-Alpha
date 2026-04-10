# -*- coding: utf-8 -*-
"""Tushare 数据源实现"""

import tushare as ts

from openclaw_alpha.core.data_source import DataSource
from openclaw_alpha.core.exceptions import MissingConfigError
from openclaw_alpha.core.settings import settings


class TushareDataSource(DataSource):
    """Tushare 数据源

    Attributes:
        name: 数据源名称 "tushare"
        required_config: 所需环境变量 ["TUSHARE_TOKEN"]
        credit: 用户积分（从 TUSHARE_CREDIT 读取，默认 0）
    """

    @property
    def name(self) -> str:
        return "tushare"

    @property
    def required_config(self) -> list[str]:
        return ["TUSHARE_TOKEN"]

    @property
    def credit(self) -> int:
        """用户积分

        Returns:
            用户积分
        """
        return settings.tushare_credit

    async def initialize(self) -> None:
        """初始化 Tushare Pro 客户端"""
        token = settings.tushare_token
        self._client = ts.pro_api(token)

    async def close(self) -> None:
        """清理资源"""
        self._client = None
        self._initialized = False
