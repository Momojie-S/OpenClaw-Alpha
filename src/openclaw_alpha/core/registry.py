# -*- coding: utf-8 -*-
"""数据源注册表"""

from openclaw_alpha.core.data_source import DataSource
from openclaw_alpha.core.exceptions import DuplicateDataSourceError


class DataSourceRegistry:
    """数据源注册表，管理数据源单例

    使用单例模式，全局只有一个实例。支持懒加载：注册时存储类，首次获取时创建实例。

    Example:
        registry = DataSourceRegistry.get_instance()
        registry.register(TushareDataSource)
        ds = registry.get("tushare")
        client = await ds.get_client()
    """

    _instance: "DataSourceRegistry | None" = None
    _data_source_classes: dict[str, type[DataSource]]
    _data_source_instances: dict[str, DataSource]

    def __new__(cls) -> "DataSourceRegistry":
        """单例模式：如果实例不存在则创建"""
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._data_source_classes = {}
            instance._data_source_instances = {}
            cls._instance = instance
        return cls._instance

    @classmethod
    def get_instance(cls) -> "DataSourceRegistry":
        """获取全局单例

        Returns:
            DataSourceRegistry 单例实例
        """
        return cls()

    def register(self, data_source_class: type[DataSource]) -> None:
        """注册数据源类型

        Args:
            data_source_class: 数据源类（不是实例）

        Raises:
            DuplicateDataSourceError: 如果名称已存在
        """
        # 创建临时实例获取名称
        temp_instance = data_source_class()
        name = temp_instance.name

        if name in self._data_source_classes:
            raise DuplicateDataSourceError(name)

        self._data_source_classes[name] = data_source_class

    def get(self, name: str) -> DataSource:
        """按名称获取数据源实例

        懒加载：首次获取时创建实例。

        Args:
            name: 数据源名称

        Returns:
            数据源实例

        Raises:
            KeyError: 如果数据源未注册
        """
        if name in self._data_source_instances:
            return self._data_source_instances[name]

        if name not in self._data_source_classes:
            raise KeyError(f"数据源未注册: {name}")

        data_source_class = self._data_source_classes[name]
        instance = data_source_class()
        self._data_source_instances[name] = instance
        return instance

    def is_available(self, name: str) -> bool:
        """检查数据源是否可用

        Args:
            name: 数据源名称

        Returns:
            True 如果数据源已注册且配置满足要求，否则 False
        """
        try:
            ds = self.get(name)
            return ds.is_available()
        except KeyError:
            return False

    async def close_all(self) -> None:
        """清理所有已初始化的数据源资源

        调用所有已创建实例的 close() 方法。
        """
        for instance in self._data_source_instances.values():
            await instance.close()

    def reset(self) -> None:
        """重置注册表

        清除所有已注册的数据源类和已创建的实例。主要用于测试场景。
        """
        self._data_source_classes.clear()
        self._data_source_instances.clear()
