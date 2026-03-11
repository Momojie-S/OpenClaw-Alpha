# -*- coding: utf-8 -*-
"""AKShare 概念板块成分股数据源"""

import asyncio
import logging
from typing import Literal

import akshare as ak
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.exceptions import DataSourceUnavailableError
from openclaw_alpha.data_sources import AkshareDataSource  # noqa: F401
from .models import ConceptConsItem
from .cache import get_cache

logger = logging.getLogger(__name__)


# 可重试的异常类型
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,  # 包括网络相关的 OSError
)


class ConceptConsFetcherAkshare(FetchMethod):
    """AKShare 概念板块成分股数据源实现

    使用 AKShare 的 stock_board_concept_cons_em 接口获取概念板块成分股数据。
    """

    name = "concept_cons_akshare"
    required_data_source = "akshare"
    priority = 10

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        reraise=True,
    )
    async def fetch(self, board_name: str) -> list[ConceptConsItem]:
        """获取概念板块成分股

        优先从缓存读取，缓存未命中时从 API 获取并缓存结果。

        Args:
            board_name: 概念板块名称

        Returns:
            概念板块成分股列表

        Raises:
            ValueError: 板块名称不存在
            ConnectionError: 网络连接失败（重试3次后）
        """
        # 1. 尝试从缓存读取
        cache = get_cache()
        cached_items = cache.get(board_name)
        if cached_items is not None:
            # 从缓存数据构建 ConceptConsItem 对象
            items = []
            for item_dict in cached_items:
                try:
                    item = ConceptConsItem(**item_dict)
                    items.append(item)
                except Exception as e:
                    logger.warning(f"构建缓存数据失败: {item_dict}, 错误: {e}")
                    continue
            return items

        # 2. 缓存未命中，从 API 获取
        logger.info(f"开始获取概念板块 '{board_name}' 成分股")

        try:
            # AKShare 函数是同步的，使用 asyncio.to_thread 包装
            df = await asyncio.to_thread(ak.stock_board_concept_cons_em, symbol=board_name)

            if df is None or df.empty:
                logger.warning(f"概念板块 '{board_name}' 无成分股数据")
                return []

            # 转换数据
            items = []
            for _, row in df.iterrows():
                try:
                    item = ConceptConsItem(
                        code=str(row.get("代码", "")).zfill(6),
                        name=str(row.get("名称", "")),
                        board_name=board_name,
                        latest_price=float(row.get("最新价", 0)),
                        change_pct=float(row.get("涨跌幅", 0)),
                        change_amount=float(row.get("涨跌额", 0)),
                        volume=float(row.get("成交量", 0)),
                        amount=float(row.get("成交额", 0)),
                        turnover_rate=float(row.get("换手率", 0)),
                        pe_ratio=float(row.get("市盈率-动态", 0)) if row.get("市盈率-动态") else 0,
                        pb_ratio=float(row.get("市净率", 0)) if row.get("市净率") else 0,
                    )
                    items.append(item)
                except (ValueError, KeyError) as e:
                    logger.warning(f"转换成分股数据失败: {row}, 错误: {e}")
                    continue

            logger.info(f"成功获取概念板块 '{board_name}' 成分股 {len(items)} 只")

            # 3. 保存到缓存
            if items:
                cache.set(board_name, [item.to_dict() for item in items])

            return items

        except Exception as e:
            error_msg = str(e)
            logger.error(f"获取概念板块成分股失败: {error_msg}")

            # 判断是否是板块不存在的错误
            if "不存在" in error_msg or "找不到" in error_msg:
                raise ValueError(
                    f"概念板块 '{board_name}' 不存在。"
                    f"请检查板块名称是否正确"
                ) from e

            # 其他错误（网络错误等）继续抛出
            raise
