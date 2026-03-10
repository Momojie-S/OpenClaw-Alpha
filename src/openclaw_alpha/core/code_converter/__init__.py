# -*- coding: utf-8 -*-
"""代码格式转换器统一入口

提供统一的代码格式转换接口，支持多数据源格式转换。
"""

import logging
from typing import Any

from .base import CodeConverter
from .cache import CodeCache
from .tushare import TushareCodeConverter
from .akshare import AKShareCodeConverter

logger = logging.getLogger(__name__)


class CodeConverterRegistry:
    """代码格式转换器注册表（单例）

    管理所有转换器，提供统一的转换接口。
    """

    _instance: "CodeConverterRegistry | None" = None

    def __new__(cls) -> "CodeConverterRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._converters: dict[str, CodeConverter] = {}
            cls._instance._cache = CodeCache()
            cls._instance._initialized = False
        return cls._instance

    def register(self, converter: CodeConverter, priority: int = 0) -> None:
        """注册转换器

        Args:
            converter: 转换器实例
            priority: 优先级（暂未使用，保留扩展）
        """
        self._converters[converter.name] = converter
        logger.debug(f"已注册代码转换器: {converter.name}")

    def get_converter(self, name: str) -> CodeConverter | None:
        """获取转换器

        Args:
            name: 转换器名称

        Returns:
            转换器实例，未找到则返回 None
        """
        return self._converters.get(name)

    def _ensure_initialized(self) -> None:
        """确保转换器已初始化"""
        if not self._initialized:
            # 注册默认转换器
            self.register(TushareCodeConverter(self._cache))
            self.register(AKShareCodeConverter(self._cache))
            self._initialized = True

    def convert(
        self, code: str, target_format: str, code_type: str | None = None
    ) -> str:
        """转换代码格式

        Args:
            code: 原始代码（可以是任意格式）
            target_format: 目标格式，如 "tushare"、"akshare"
            code_type: 代码类型（可选），如 "stock"、"etf"

        Returns:
            目标格式的代码

        Raises:
            ValueError: 目标格式不支持
        """
        self._ensure_initialized()

        # 获取目标转换器
        converter = self.get_converter(target_format)
        if converter is None:
            raise ValueError(
                f"不支持的代码格式: {target_format}。支持的格式: {list(self._converters.keys())}"
            )

        return converter.convert(code, target_format, code_type)

    def normalize(self, code: str) -> str:
        """标准化为无后缀代码

        Args:
            code: 任意格式的代码

        Returns:
            无后缀的标准代码
        """
        self._ensure_initialized()

        # 使用第一个可用的转换器标准化
        for converter in self._converters.values():
            return converter.normalize(code)

        # 降级处理：直接去掉后缀
        code = code.upper()
        for suffix in [".SZ", ".SH", ".HK", ".BJ"]:
            if code.endswith(suffix):
                code = code[: -len(suffix)]
                break
        return code

    def convert_batch(
        self, codes: list[str], target_format: str, code_type: str | None = None
    ) -> list[str]:
        """批量转换代码格式

        Args:
            codes: 原始代码列表
            target_format: 目标格式
            code_type: 代码类型（可选）

        Returns:
            目标格式的代码列表
        """
        return [
            self.convert(code, target_format, code_type) for code in codes
        ]


# 全局注册表实例
_registry = CodeConverterRegistry()


def convert_code(
    code: str, target_format: str, code_type: str | None = None
) -> str:
    """转换代码格式

    Args:
        code: 原始代码（可以是任意格式）
        target_format: 目标格式，如 "tushare"、"akshare"
        code_type: 代码类型（可选），如 "stock"、"etf"

    Returns:
        目标格式的代码

    Examples:
        >>> convert_code("000001", "tushare")
        "000001.SZ"
        >>> convert_code("000001.SZ", "akshare")
        "000001"
    """
    return _registry.convert(code, target_format, code_type)


def normalize_code(code: str) -> str:
    """标准化为无后缀代码

    Args:
        code: 任意格式的代码

    Returns:
        无后缀的标准代码

    Examples:
        >>> normalize_code("000001.SZ")
        "000001"
        >>> normalize_code("hk00700")
        "00700"
    """
    return _registry.normalize(code)


def convert_codes(
    codes: list[str], target_format: str, code_type: str | None = None
) -> list[str]:
    """批量转换代码格式

    Args:
        codes: 原始代码列表
        target_format: 目标格式
        code_type: 代码类型（可选）

    Returns:
        目标格式的代码列表

    Examples:
        >>> convert_codes(["000001", "600519"], "tushare")
        ["000001.SZ", "600519.SH"]
    """
    return _registry.convert_batch(codes, target_format, code_type)


def refresh_cache(converter_name: str | None = None) -> None:
    """刷新代码缓存

    Args:
        converter_name: 转换器名称，为 None 则刷新所有
    """
    _registry._ensure_initialized()

    if converter_name:
        converter = _registry.get_converter(converter_name)
        if converter:
            converter.refresh_cache()
    else:
        for converter in _registry._converters.values():
            converter.refresh_cache()
