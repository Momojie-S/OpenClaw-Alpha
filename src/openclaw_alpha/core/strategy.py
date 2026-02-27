# -*- coding: utf-8 -*-
"""策略基类"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from openclaw_alpha.core.exceptions import NoAvailableImplementationError
from openclaw_alpha.core.registry import DataSourceRegistry

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class Strategy(ABC, Generic[TInput, TOutput]):
    """策略基类

    支持泛型的入参和出参类型。子类需要声明 _data_source_names 并实现 run() 方法。

    Attributes:
        _data_source_names: 依赖的数据源名称列表，用于可用性检查

    Example:
        class StockQuoteTushare(Strategy[str, Quote]):
            _data_source_names = ["tushare"]

            async def run(self, symbol: str) -> Quote:
                client = await Strategy.get_client("tushare")
                return client.get_quote(symbol)
    """

    _data_source_names: list[str] = []

    @staticmethod
    async def get_client(name: str) -> Any:
        """从注册表获取数据源客户端

        便捷静态方法，供策略实现获取数据源客户端。

        Args:
            name: 数据源名称

        Returns:
            数据源客户端实例
        """
        registry = DataSourceRegistry.get_instance()
        ds = registry.get(name)
        client = await ds.get_client()
        return client

    @abstractmethod
    async def run(self, input: TInput) -> TOutput:
        """执行策略逻辑

        Args:
            input: 策略输入

        Returns:
            策略输出
        """
        pass


class StrategyEntry(Strategy[TInput, TOutput]):
    """策略入口基类

    管理多个实现，运行时自动选择可用的实现执行。

    Example:
        entry = StockQuoteStrategy()
        entry.register(StockQuoteTushare(), priority=1)
        entry.register(StockQuoteAkshare(), priority=2)
        quote = await entry.run("000001")
    """

    def __init__(self) -> None:
        self._implementations: list[
            tuple[list[str], Strategy[TInput, TOutput], int]
        ] = []

    def register(self, impl: Strategy[TInput, TOutput], priority: int = 0) -> None:
        """注册一个实现

        从实现的 _data_source_names 读取数据源依赖。

        Args:
            impl: 策略实现实例
            priority: 优先级，数值越大优先级越高
        """
        data_source_names = impl._data_source_names
        self._implementations.append((data_source_names, impl, priority))

    def _select_implementation(self) -> Strategy[TInput, TOutput]:
        """选择优先级最高且数据源都可用的实现

        Returns:
            可用的策略实现

        Raises:
            NoAvailableImplementationError: 如果所有实现的数据源都不可用
        """
        # 按优先级降序排序
        sorted_impls = sorted(
            self._implementations,
            key=lambda x: x[2],
            reverse=True,
        )

        registry = DataSourceRegistry.get_instance()
        checked: list[str] = []

        for data_source_names, impl, _ in sorted_impls:
            impl_name = impl.__class__.__name__
            checked.append(impl_name)

            # 检查所有数据源是否可用
            all_available = True
            for ds_name in data_source_names:
                if not registry.is_available(ds_name):
                    all_available = False
                    break

            if all_available:
                return impl

        raise NoAvailableImplementationError(self.__class__.__name__, checked)

    async def run(self, input: TInput) -> TOutput:
        """选择可用的实现并执行

        Args:
            input: 策略输入

        Returns:
            策略输出

        Raises:
            NoAvailableImplementationError: 如果所有实现的数据源都不可用
        """
        impl = self._select_implementation()
        return await impl.run(input)
