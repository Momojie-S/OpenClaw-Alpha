# -*- coding: utf-8 -*-
"""AKShare 数据源实现"""

from openclaw_alpha.core.data_source import DataSource


class AkshareDataSource(DataSource):
    """AKShare 数据源

    无需任何配置即可使用。
    """

    @property
    def name(self) -> str:
        """数据源名称"""
        return "akshare"

    @property
    def required_config(self) -> list[str]:
        """所需的环境变量配置项列表（空列表，无需配置）"""
        return []

    async def initialize(self) -> None:
        """初始化数据源

        AKShare 不需要特殊的初始化操作。
        """
        # AKShare 是同步库，直接导入即可
        import akshare as ak

        self._client = ak

    async def close(self) -> None:
        """清理资源"""
        self._client = None
        self._initialized = False
