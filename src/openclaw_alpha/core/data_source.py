# -*- coding: utf-8 -*-
"""数据源基类"""

import asyncio
import os
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TClient = TypeVar("TClient")


class DataSource(ABC, Generic[TClient]):
    """数据源基类

    泛型 TClient 为客户端类型。子类需要实现 name 和 required_config 抽象属性。

    Attributes:
        name: 数据源名称，用于注册表索引
        required_config: 所需的环境变量配置项列表
    """

    def __init__(self) -> None:
        self._client: TClient | None = None
        self._initialized: bool = False
        self._lock: asyncio.Lock = asyncio.Lock()

    @property
    @abstractmethod
    def name(self) -> str:
        """数据源名称，用于注册表索引"""
        pass

    @property
    @abstractmethod
    def required_config(self) -> list[str]:
        """所需的环境变量配置项列表"""
        pass

    def is_available(self) -> bool:
        """检查当前环境是否满足数据源要求

        Returns:
            True 如果所有 required_config 中的环境变量都已设置，否则 False
        """
        for config_key in self.required_config:
            value = os.getenv(config_key)
            if value is None or value == "":
                return False
        return True

    async def initialize(self) -> None:
        """初始化数据源，创建客户端连接

        子类应该重写此方法来实现具体的初始化逻辑。
        """
        pass

    async def get_client(self) -> TClient:
        """获取数据源客户端

        懒加载模式：首次调用时自动初始化。使用 asyncio.Lock 保护并发初始化。

        Returns:
            数据源客户端实例

        Raises:
            RuntimeError: 如果初始化失败
        """
        if self._initialized and self._client is not None:
            return self._client

        async with self._lock:
            # 双重检查，防止并发时重复初始化
            if self._initialized and self._client is not None:
                return self._client

            await self.initialize()
            self._initialized = True

        if self._client is None:
            raise RuntimeError(f"数据源 {self.name} 初始化失败：客户端未创建")

        return self._client

    async def close(self) -> None:
        """清理资源

        子类应该重写此方法来清理客户端连接等资源。
        重写时应该调用 super().close() 或手动设置 _initialized = False。
        """
        self._client = None
        self._initialized = False
