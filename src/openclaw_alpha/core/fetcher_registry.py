# -*- coding: utf-8 -*-
"""Fetcher 注册表"""

from openclaw_alpha.core.exceptions import DuplicateFetcherError
from openclaw_alpha.core.fetcher import DataFetcher


class FetcherRegistry:
    """Fetcher 注册表，管理 DataFetcher 实例

    使用单例模式，全局只有一个实例。支持按名称和按数据类型查询。

    Example:
        registry = FetcherRegistry.get_instance()
        registry.register(ConceptBoardTushareFetcher())
        fetcher = registry.get("tushare_concept")
        fetchers = registry.get_available("concept_board")
    """

    _instance: "FetcherRegistry | None" = None
    _fetchers: dict[str, DataFetcher]

    def __new__(cls) -> "FetcherRegistry":
        """单例模式：如果实例不存在则创建"""
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._fetchers = {}
            cls._instance = instance
        return cls._instance

    @classmethod
    def get_instance(cls) -> "FetcherRegistry":
        """获取全局单例

        Returns:
            FetcherRegistry 单例实例
        """
        return cls()

    def register(self, fetcher: DataFetcher) -> None:
        """注册 Fetcher 实例

        Args:
            fetcher: DataFetcher 实例

        Raises:
            DuplicateFetcherError: 如果名称已存在
        """
        name = fetcher.name
        if name in self._fetchers:
            raise DuplicateFetcherError(name)

        self._fetchers[name] = fetcher

    def get(self, name: str) -> DataFetcher:
        """按名称获取 Fetcher 实例

        Args:
            name: Fetcher 名称

        Returns:
            DataFetcher 实例

        Raises:
            KeyError: 如果 Fetcher 未注册
        """
        if name not in self._fetchers:
            raise KeyError(f"Fetcher 未注册: {name}")
        return self._fetchers[name]

    def get_by_data_type(self, data_type: str) -> list[DataFetcher]:
        """按数据类型获取所有 Fetcher

        Args:
            data_type: 数据类型

        Returns:
            该数据类型的所有 Fetcher 列表（可能为空）
        """
        return [f for f in self._fetchers.values() if f.data_type == data_type]

    def get_available(self, data_type: str) -> list[DataFetcher]:
        """按数据类型获取所有可用的 Fetcher

        可用是指数据源配置满足（is_available() 返回 True）。
        结果按 priority 降序排列（数值大的在前）。

        Args:
            data_type: 数据类型

        Returns:
            可用的 Fetcher 列表，按优先级降序排列（可能为空）
        """
        fetchers = self.get_by_data_type(data_type)
        available = [f for f in fetchers if f.is_available()]
        # 按优先级降序排列
        return sorted(available, key=lambda f: f.priority, reverse=True)

    def reset(self) -> None:
        """重置注册表

        清除所有已注册的 Fetcher。主要用于测试场景。
        """
        self._fetchers.clear()
