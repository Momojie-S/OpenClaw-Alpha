# -*- coding: utf-8 -*-
"""策略框架异常类"""


class DuplicateDataSourceError(Exception):
    """数据源名称重复异常

    当尝试注册一个已存在名称的数据源时抛出。

    Args:
        name: 重复的数据源名称
    """

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"数据源名称已存在: {name}")


class NoAvailableImplementationError(Exception):
    """无可用实现异常

    当策略入口的所有实现的数据源都不可用时抛出。

    Args:
        strategy_name: 策略名称
        checked_implementations: 已检查的实现列表
    """

    def __init__(self, strategy_name: str, checked_implementations: list[str]) -> None:
        self.strategy_name = strategy_name
        self.checked_implementations = checked_implementations
        impl_str = (
            ", ".join(checked_implementations) if checked_implementations else "无"
        )
        super().__init__(
            f"策略 '{strategy_name}' 没有可用的实现。已检查的实现: [{impl_str}]"
        )
