# -*- coding: utf-8 -*-
"""框架异常类"""


class NoAvailableMethodError(Exception):
    """无可用实现异常

    当 Fetcher 的所有 FetchMethod 对应的数据源都不可用时抛出。

    Args:
        fetcher_name: Fetcher 名称
        checked_methods: 已检查的 Method 列表
        errors: 所有失败原因
    """

    def __init__(
        self,
        fetcher_name: str,
        checked_methods: list[str],
        errors: list["DataSourceUnavailableError"] | None = None,
    ) -> None:
        self.fetcher_name = fetcher_name
        self.checked_methods = checked_methods
        self.errors = errors or []

        # 整合错误信息
        if self.errors:
            error_msgs = []
            for err in self.errors:
                if isinstance(err, MissingConfigError):
                    keys_str = ", ".join(err.missing_keys)
                    error_msgs.append(f"{err.data_source_name}: 缺少配置 [{keys_str}]")
                elif isinstance(err, InsufficientCreditError):
                    error_msgs.append(
                        f"{err.data_source_name}: 积分不足（需要 {err.required}，实际 {err.actual}）"
                    )
                else:
                    error_msgs.append(f"{err.data_source_name}: {err.reason}")
            detail = "\n".join(f"  - {msg}" for msg in error_msgs)
            message = f"Fetcher '{fetcher_name}' 所有数据源均不可用:\n{detail}"
        else:
            methods_str = ", ".join(checked_methods) if checked_methods else "无"
            message = f"Fetcher '{fetcher_name}' 没有可用的实现。已检查: [{methods_str}]"

        super().__init__(message)


# =============================================================================
# 数据源不可用相关异常
# =============================================================================


class DataSourceUnavailableError(Exception):
    """数据源不可用异常基类

    所有数据源不可用相关的异常应继承此类。

    Attributes:
        data_source_name: 数据源名称
        reason: 具体原因
    """

    def __init__(self, data_source_name: str, reason: str) -> None:
        self.data_source_name = data_source_name
        self.reason = reason
        super().__init__(f"数据源 '{data_source_name}' 不可用: {reason}")


class MissingConfigError(DataSourceUnavailableError):
    """配置缺失异常

    当数据源所需的环境变量未配置时抛出。

    Attributes:
        missing_keys: 缺失的环境变量列表
    """

    def __init__(self, data_source_name: str, missing_keys: list[str]) -> None:
        self.missing_keys = missing_keys
        keys_str = ", ".join(missing_keys)
        super().__init__(data_source_name, f"缺少配置 [{keys_str}]")


class InsufficientCreditError(DataSourceUnavailableError):
    """积分不足异常

    当用户积分不满足数据源要求时抛出。

    Attributes:
        required: 需要的积分
        actual: 实际积分
    """

    def __init__(self, data_source_name: str, required: int, actual: int) -> None:
        self.required = required
        self.actual = actual
        super().__init__(
            data_source_name, f"积分不足（需要 {required}，实际 {actual}）"
        )


class DuplicateDataSourceError(Exception):
    """重复数据源异常

    当尝试注册已存在的数据源时抛出。

    Args:
        name: 重复的数据源名称
    """

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"数据源 '{name}' 已注册，不能重复注册")


class UnregisteredDataSourceError(Exception):
    """数据源未注册异常

    当尝试获取未注册的数据源时抛出。

    Args:
        name: 未注册的数据源名称
    """

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(
            f"内部错误：数据源 '{name}' 未注册。"
            f"这是代码 bug，请联系开发者并提供：数据源名称={name}、触发时间"
        )


# =============================================================================
# API 重试相关异常
# =============================================================================


class RetryableError(Exception):
    """可重试异常基类

    临时性故障，重试可能成功。所有可重试异常应继承此类。
    """

    pass


class RateLimitError(RetryableError):
    """请求限流异常

    当 API 请求频率超过限制时抛出（HTTP 429）。
    """

    pass


class TimeoutError(RetryableError):
    """请求超时异常

    当 API 请求超时时抛出。
    """

    pass


class ServerError(RetryableError):
    """服务端错误异常

    当 API 返回服务端错误时抛出（HTTP 5xx）。
    """

    pass


class NetworkError(RetryableError):
    """网络连接异常

    当网络连接出现问题时抛出。
    """

    pass


class AuthenticationError(Exception):
    """认证失败异常

    当 API 认证失败时抛出（HTTP 401）。此异常不可重试。
    """

    pass


class PermissionError(Exception):
    """权限不足异常

    当 API 请求权限不足时抛出（HTTP 403）。此异常不可重试。
    """

    pass


class NotFoundError(Exception):
    """资源不存在异常

    当请求的资源不存在时抛出（HTTP 404）。此异常不可重试。
    """

    pass


class ValidationError(Exception):
    """参数验证失败异常

    当请求参数验证失败时抛出（HTTP 400）。此异常不可重试。
    """

    pass
