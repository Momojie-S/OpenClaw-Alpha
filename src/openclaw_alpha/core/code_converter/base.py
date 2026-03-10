# -*- coding: utf-8 -*-
"""代码格式转换器基类"""

from abc import ABC, abstractmethod


class CodeConverter(ABC):
    """代码格式转换器基类

    负责将股票代码在不同数据源格式间转换。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """转换器名称

        Returns:
            转换器标识，如 "tushare"、"akshare"
        """
        pass

    @property
    @abstractmethod
    def data_source(self) -> str:
        """对应的数据源名称

        Returns:
            数据源标识，与 DataSourceRegistry 中的名称对应
        """
        pass

    @property
    @abstractmethod
    def supported_types(self) -> list[str]:
        """支持的代码类型

        Returns:
            支持的类型列表，如 ["stock", "index", "etf", "hk", "us"]
        """
        pass

    @abstractmethod
    def convert(
        self, code: str, target_format: str, code_type: str | None = None
    ) -> str:
        """转换代码格式

        Args:
            code: 原始代码（可以是任意格式）
            target_format: 目标格式，如 "tushare"、"akshare"
            code_type: 代码类型（可选），如 "stock"、"etf"，用于提高匹配准确性

        Returns:
            目标格式的代码

        Raises:
            ValueError: 代码格式无法识别或转换失败
        """
        pass

    @abstractmethod
    def normalize(self, code: str) -> str:
        """标准化为无后缀代码

        Args:
            code: 任意格式的代码

        Returns:
            无后缀的标准代码，如 "000001"、"600519"
        """
        pass

    @abstractmethod
    def refresh_cache(self) -> None:
        """刷新缓存

        从数据源重新获取代码列表并更新本地缓存。
        """
        pass

    def format_code(self, code: str, suffix: str) -> str:
        """格式化代码（添加后缀）

        Args:
            code: 无后缀的标准代码
            suffix: 后缀，如 ".SZ"、".SH"

        Returns:
            格式化后的代码，如 "000001.SZ"
        """
        normalized = self.normalize(code)
        return f"{normalized}{suffix}"
