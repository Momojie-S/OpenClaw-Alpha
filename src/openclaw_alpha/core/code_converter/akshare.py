# -*- coding: utf-8 -*-
"""AKShare 代码格式转换器"""

import logging
from typing import Any

from .base import CodeConverter
from .cache import CodeCache

logger = logging.getLogger(__name__)


class AKShareCodeConverter(CodeConverter):
    """AKShare 代码格式转换器

    支持 A 股、指数、ETF、港股、美股代码格式转换。
    AKShare 多数接口使用无后缀代码，部分接口需要带市场前缀。
    """

    def __init__(self, cache: CodeCache | None = None):
        """初始化转换器

        Args:
            cache: 缓存管理器，为 None 则使用默认配置
        """
        self._cache = cache or CodeCache()
        self._codes_cache: dict[str, dict[str, Any]] = {}

    @property
    def name(self) -> str:
        return "akshare"

    @property
    def data_source(self) -> str:
        return "akshare"

    @property
    def supported_types(self) -> list[str]:
        return ["stock", "index", "etf", "hk", "us"]

    def normalize(self, code: str) -> str:
        """标准化为无后缀代码

        Args:
            code: 任意格式的代码

        Returns:
            无后缀的标准代码
        """
        # 去掉可能的后缀
        code = code.upper()
        for suffix in [".SZ", ".SH", ".HK", ".BJ"]:
            if code.endswith(suffix):
                code = code[: -len(suffix)]
                break

        # 去掉港股前缀（如 hk00700 -> 00700）
        if code.lower().startswith("hk"):
            code = code[2:]

        return code

    def convert(
        self, code: str, target_format: str, code_type: str | None = None
    ) -> str:
        """转换代码格式

        Args:
            code: 原始代码
            target_format: 目标格式
            code_type: 代码类型（可选）

        Returns:
            目标格式的代码
        """
        normalized = self.normalize(code)

        # 如果目标格式是 akshare，返回无后缀代码
        if target_format == "akshare":
            return normalized

        # 其他格式暂不支持（由对应的转换器处理）
        return normalized

    def refresh_cache(self) -> None:
        """刷新缓存

        AKShare 转换器通常不需要缓存，因为使用规则即可推断。
        但保留接口以备将来扩展。
        """
        logger.info("AKShare 转换器无需刷新缓存")
