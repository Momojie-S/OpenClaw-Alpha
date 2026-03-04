# -*- coding: utf-8 -*-
"""数据加工器基类"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from openclaw_alpha.core.exceptions import NoAvailableFetcherError
from openclaw_alpha.core.fetcher import DataFetcher
from openclaw_alpha.core.fetcher_registry import FetcherRegistry

TProcessParams = TypeVar("TProcessParams")
TProcessResult = TypeVar("TProcessResult")


class DataProcessor(ABC, Generic[TProcessParams, TProcessResult]):
    """数据加工器基类

    组合多个 Fetcher，只做数据加工，不直接获取数据。
    权限需求可自动计算（按 data_type 分组，组内 OR，组间 AND）。

    Attributes:
        name: Processor 标识
        required_data_types: 需要的数据类型列表

    Example:
        class IndustryTrendProcessor(
            DataProcessor[IndustryTrendParams, IndustryTrendResult]
        ):
            name = "industry_trend"
            required_data_types = ["concept_board", "sw_industry"]

            async def process(
                self, params: IndustryTrendParams
            ) -> IndustryTrendResult:
                # 获取 concept_board 数据
                concept_fetcher = self.get_available_fetcher("concept_board")
                concept_data = await concept_fetcher.fetch(...)

                # 获取 sw_industry 数据
                industry_fetcher = self.get_available_fetcher("sw_industry")
                industry_data = await industry_fetcher.fetch(...)

                # 加工数据...
    """

    name: str
    required_data_types: list[str]

    def get_available_fetcher(self, data_type: str) -> DataFetcher:
        """获取指定数据类型的可用 Fetcher

        从 FetcherRegistry 获取可用的 Fetcher，优先选择高优先级的实现。

        Args:
            data_type: 数据类型

        Returns:
            可用的 Fetcher 实例

        Raises:
            NoAvailableFetcherError: 如果没有可用的 Fetcher
        """
        registry = FetcherRegistry.get_instance()
        available = registry.get_available(data_type)

        if not available:
            raise NoAvailableFetcherError(data_type)

        # 返回优先级最高的（已按 priority 降序排列）
        return available[0]

    def get_all_available_fetchers(self, data_type: str) -> list[DataFetcher]:
        """获取指定数据类型的所有可用 Fetcher

        Args:
            data_type: 数据类型

        Returns:
            可用的 Fetcher 列表，按优先级降序排列（可能为空）
        """
        registry = FetcherRegistry.get_instance()
        return registry.get_available(data_type)

    def check_availability(self) -> tuple[bool, list[str]]:
        """检查 Processor 是否可用

        检查所有 required_data_types 是否都有可用的 Fetcher。

        Returns:
            元组 (是否可用, 不可用的 data_type 列表)
        """
        unavailable: list[str] = []
        for data_type in self.required_data_types:
            fetcher = self.get_all_available_fetchers(data_type)
            if not fetcher:
                unavailable.append(data_type)

        return len(unavailable) == 0, unavailable

    @abstractmethod
    async def process(self, params: TProcessParams) -> TProcessResult:
        """执行数据加工

        Args:
            params: 加工参数

        Returns:
            加工结果
        """
        pass
