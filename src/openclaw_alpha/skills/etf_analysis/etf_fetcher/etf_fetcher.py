# -*- coding: utf-8 -*-
"""ETF 数据 Fetcher 入口"""

import logging
from typing import Any

from openclaw_alpha.core.fetcher import Fetcher
from openclaw_alpha.core.exceptions import DataSourceUnavailableError, NoAvailableMethodError
from .akshare_impl import EtfFetcherAkshare
from .tushare_impl import EtfFetcherTushare

logger = logging.getLogger(__name__)


class EtfFetcher(Fetcher):
    """ETF 数据获取器

    支持：
    - Tushare：历史数据（5000积分）
    - AKShare（新浪财经）：实时行情 + 历史数据

    注意：获取全部 ETF 实时行情时，Tushare API 不支持（需要 ts_code 或 trade_date），
    会自动 fallback 到 AKShare。
    """

    name = "etf"

    def __init__(self):
        """初始化并注册实现"""
        super().__init__()
        # 注册实现（优先级：Tushare > AKShare）
        self.register(EtfFetcherTushare(), priority=20)
        self.register(EtfFetcherAkshare(), priority=10)

    async def fetch(self, params: dict[str, Any]) -> dict[str, Any]:
        """获取 ETF 数据，支持 fallback

        当 Tushare 实现失败时（如获取全部实时行情），自动尝试 AKShare 实现。

        Args:
            params: 参数字典

        Returns:
            ETF 数据字典
        """
        # 按优先级排序
        sorted_methods = sorted(self._methods, key=lambda m: m.priority, reverse=True)

        errors: list[DataSourceUnavailableError] = []

        for method in sorted_methods:
            # 检查方法是否可用（配置、积分）
            available, error = method.is_available()
            if not available:
                if error:
                    errors.append(error)
                continue

            try:
                result = await method.fetch(params)
                # 确保返回格式一致（字典）
                if isinstance(result, list):
                    # Tushare 返回列表，需要包装
                    return {
                        "data": result,
                        "count": len(result),
                    }
                return result
            except DataSourceUnavailableError as e:
                logger.info(f"{method.name} 不可用: {e.reason}，尝试下一个实现")
                errors.append(e)
                continue
            except Exception as e:
                logger.error(f"{method.name} 执行失败: {e}")
                errors.append(
                    DataSourceUnavailableError(
                        data_source_name=method.required_data_source,
                        reason=f"执行失败: {e}",
                    )
                )
                continue

        # 所有实现都失败
        checked_methods = [
            f"{m.name}(ds={m.required_data_source})"
            for m in sorted_methods
        ]
        raise NoAvailableMethodError(self.name, checked_methods, errors)
