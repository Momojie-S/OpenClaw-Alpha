# -*- coding: utf-8 -*-
"""数据获取器基类"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from openclaw_alpha.core.registry import DataSourceRegistry

TFetchParams = TypeVar("TFetchParams")
TFetchResult = TypeVar("TFetchResult")


class DataFetcher(ABC, Generic[TFetchParams, TFetchResult]):
    """数据获取器基类

    专门负责获取某一类数据，一个实现只用一种数据源。
    用于注册表索引，支持按 data_type 分组和优先级选择。

    Attributes:
        name: Fetcher 标识，如 `tushare_concept`
        data_type: 数据类型，如 `concept_board`（用于分组和 OR 关系）
        required_data_source: 需要的数据源名称（单一数据源）
        priority: 优先级（数值越大越优先，默认为 0）

    Example:
        class ConceptBoardTushareFetcher(
            DataFetcher[ConceptBoardParams, list[ConceptBoard]]
        ):
            name = "tushare_concept"
            data_type = "concept_board"
            required_data_source = "tushare"
            priority = 1

            async def fetch(self, params: ConceptBoardParams) -> list[ConceptBoard]:
                client = await self.get_client()
                # 获取数据...
    """

    name: str
    data_type: str
    required_data_source: str
    priority: int = 0

    @staticmethod
    async def get_client(name: str) -> Any:
        """从注册表获取数据源客户端

        便捷静态方法，供 Fetcher 实现获取数据源客户端。

        Args:
            name: 数据源名称

        Returns:
            数据源客户端实例
        """
        registry = DataSourceRegistry.get_instance()
        ds = registry.get(name)
        client = await ds.get_client()
        return client

    def is_available(self) -> bool:
        """检查数据源是否可用

        Returns:
            True 如果 required_data_source 对应的数据源配置满足，否则 False
        """
        registry = DataSourceRegistry.get_instance()
        return registry.is_available(self.required_data_source)

    @abstractmethod
    async def fetch(self, params: TFetchParams) -> TFetchResult:
        """获取数据

        Args:
            params: 获取参数

        Returns:
            获取结果
        """
        pass
