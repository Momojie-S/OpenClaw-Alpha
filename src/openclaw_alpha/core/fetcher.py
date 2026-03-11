# -*- coding: utf-8 -*-
"""数据获取器基类"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from openclaw_alpha.core.exceptions import (
    DataSourceUnavailableError,
    InsufficientCreditError,
    MissingConfigError,
    NoAvailableMethodError,
    UnregisteredDataSourceError,
)
from openclaw_alpha.core.registry import DataSourceRegistry

logger = logging.getLogger(__name__)


class FetchMethod(ABC):
    """Fetcher 实现基类

    负责具体的数据获取逻辑，绑定单一数据源。

    Attributes:
        name: Method 标识
        required_data_source: 需要的数据源名称
        required_credit: 需要的积分（仅 Tushare，默认 0 表示无积分要求）
        priority: 优先级（数值越大越优先）
    """

    name: str
    required_data_source: str
    required_credit: int = 0
    priority: int = 0

    async def get_client(self) -> Any:
        """获取数据源客户端

        Returns:
            数据源客户端实例
        """
        registry = DataSourceRegistry.get_instance()
        ds = registry.get(self.required_data_source)
        return await ds.get_client()

    def is_available(self) -> tuple[bool, DataSourceUnavailableError | None]:
        """检查方法是否可用

        检查数据源配置是否满足要求（token + 积分）。

        Returns:
            (是否可用, 失败原因) 元组。可用时失败原因为 None。
        """
        registry = DataSourceRegistry.get_instance()

        # 检查数据源是否注册
        try:
            ds = registry.get(self.required_data_source)
        except UnregisteredDataSourceError:
            return (
                False,
                DataSourceUnavailableError(
                    data_source_name=self.required_data_source,
                    reason="数据源未注册",
                ),
            )

        # 检查数据源配置（token 等）
        if not ds.is_available():
            return (
                False,
                MissingConfigError(
                    data_source_name=self.required_data_source,
                    missing_keys=ds.required_config,
                ),
            )

        # 检查积分（仅对有积分要求且数据源支持积分的情况）
        if self.required_credit > 0:
            if hasattr(ds, "credit"):
                user_credit = ds.credit  # type: ignore
                if user_credit < self.required_credit:
                    return (
                        False,
                        InsufficientCreditError(
                            data_source_name=self.required_data_source,
                            required=self.required_credit,
                            actual=user_credit,
                        ),
                    )

        return (True, None)

    @abstractmethod
    async def fetch(self, *args: Any, **kwargs: Any) -> Any:
        """执行数据获取

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            获取的数据
        """
        pass


class Fetcher:
    """Fetcher 入口基类

    负责注册和调度，按优先级尝试每个可用的 FetchMethod，
    执行失败时自动降级到下一个。

    子类需要：
    1. 定义 name 属性
    2. 在 __init__ 中调用 register() 注册各个 FetchMethod
    """

    name: str

    def __init__(self) -> None:
        self._methods: list[FetchMethod] = []

    def register(self, method: FetchMethod, priority: int | None = None) -> None:
        """注册 FetchMethod

        Args:
            method: FetchMethod 实例
            priority: 优先级（可选，覆盖 method 自身的 priority）
        """
        if priority is not None:
            method.priority = priority
        self._methods.append(method)

    async def fetch(self, *args: Any, **kwargs: Any) -> Any:
        """选择可用实现并执行数据获取（支持自动降级）

        按优先级尝试每个可用的 method，如果执行失败（抛出任何异常），
        则降级到下一个可用的 method。

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            获取的数据

        Raises:
            NoAvailableMethodError: 如果所有实现都不可用或全部执行失败
        """
        # 按优先级排序（降序）
        sorted_methods = sorted(self._methods, key=lambda m: m.priority, reverse=True)

        # 收集所有错误（检查阶段 + 执行阶段）
        check_errors: list[DataSourceUnavailableError] = []
        exec_errors: list[Exception] = []

        for method in sorted_methods:
            # 检查可用性
            available, error = method.is_available()
            if not available:
                if error:
                    logger.info(f"FetchMethod {method.name} 检查失败: {error.reason}")
                    check_errors.append(error)
                continue

            # 尝试执行（任何异常都降级）
            try:
                logger.debug(f"FetchMethod {method.name} 开始执行")
                result = await method.fetch(*args, **kwargs)
                logger.info(f"FetchMethod {method.name} 执行成功")
                return result
            except Exception as e:
                logger.warning(
                    f"FetchMethod {method.name} 执行失败，尝试降级: {type(e).__name__}: {e}"
                )
                exec_errors.append(e)
                continue

        # 所有 method 都不可用或执行失败
        checked_methods = [
            f"{m.name}(ds={m.required_data_source}, credit={m.required_credit})"
            for m in self._methods
        ]
        all_errors = check_errors + exec_errors
        raise NoAvailableMethodError(self.name, checked_methods, all_errors)
