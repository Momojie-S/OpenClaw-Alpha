# -*- coding: utf-8 -*-
"""Tushare 代码格式转换器"""

import asyncio
import logging
from typing import Any

from .base import CodeConverter
from .cache import CodeCache

logger = logging.getLogger(__name__)


class TushareCodeConverter(CodeConverter):
    """Tushare 代码格式转换器

    支持 A 股、指数、ETF、港股、美股代码格式转换。
    使用 Tushare API 获取代码列表，缓存到本地。
    """

    def __init__(self, cache: CodeCache | None = None):
        """初始化转换器

        Args:
            cache: 缓存管理器，为 None 则使用默认配置
        """
        self._cache = cache or CodeCache()
        self._codes_cache: dict[str, dict[str, Any]] = {}
        self._tushare_client = None

    @property
    def name(self) -> str:
        return "tushare"

    @property
    def data_source(self) -> str:
        return "tushare"

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
        # 先去掉可能的后缀（大小写不敏感）
        code_upper = code.upper()
        for suffix in [".SZ", ".SH", ".HK", ".BJ"]:
            if code_upper.endswith(suffix):
                code = code[: -len(suffix)]
                break
        return code.upper()

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

        # 如果目标格式不是 tushare，先标准化
        if target_format != "tushare":
            return normalized

        # 转换为 Tushare 格式
        return self._to_tushare_format(normalized, code_type)

    def _to_tushare_format(self, code: str, code_type: str | None = None) -> str:
        """转换为 Tushare 格式

        Args:
            code: 标准化的代码
            code_type: 代码类型（可选）

        Returns:
            Tushare 格式代码
        """
        # 如果指定了类型，优先从该类型查找
        if code_type:
            suffix = self._get_suffix_by_type(code, code_type)
            if suffix:
                return self.format_code(code, suffix)

        # 尝试从缓存中查找市场信息
        for ctype in self.supported_types:
            suffix = self._get_suffix_by_type(code, ctype)
            if suffix:
                return self.format_code(code, suffix)

        # 缓存中没有，使用规则推断（仅支持 A 股）
        return self._infer_tushare_format(code)

    def _get_suffix_by_type(self, code: str, code_type: str) -> str | None:
        """根据代码类型从缓存中获取后缀

        Args:
            code: 标准化的代码
            code_type: 代码类型

        Returns:
            后缀（如 ".SZ"、".SH"），未找到则返回 None
        """
        # 确保缓存已加载
        if code_type not in self._codes_cache:
            cached_data = self._cache.load(self.name, code_type)
            if cached_data:
                self._codes_cache[code_type] = cached_data
            else:
                return None

        codes_dict = self._codes_cache.get(code_type, {})
        code_info = codes_dict.get(code)

        if code_info:
            market = code_info.get("market", "").upper()
            if market == "SH":
                return ".SH"
            elif market == "SZ":
                return ".SZ"
            elif market == "BJ":
                return ".BJ"

        return None

    def _infer_tushare_format(self, code: str) -> str:
        """使用规则推断 Tushare 格式（仅支持 A 股）

        Args:
            code: 标准化的代码

        Returns:
            Tushare 格式代码
        """
        # A 股规则推断
        if code.startswith("6"):
            # 60xxxx, 68xxxx 为上海
            return self.format_code(code, ".SH")
        elif code.startswith(("0", "3")):
            # 00xxxx, 30xxxx 为深圳
            return self.format_code(code, ".SZ")
        elif code.startswith("8") or code.startswith("4"):
            # 8xxxxx, 4xxxxx 为北交所
            return self.format_code(code, ".BJ")
        else:
            # 无法推断，默认返回原代码
            return code

    def refresh_cache(self) -> None:
        """刷新缓存

        从 Tushare API 获取代码列表并更新本地缓存。
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(self._refresh_cache_async())

    async def _refresh_cache_async(self) -> None:
        """异步刷新缓存"""
        # 获取 Tushare 客户端
        client = await self._get_tushare_client()
        if client is None:
            logger.warning("Tushare 客户端不可用，无法刷新缓存")
            return

        # 刷新各类型的缓存
        await self._refresh_stock_cache(client)
        await self._refresh_index_cache(client)
        await self._refresh_etf_cache(client)

    async def _get_tushare_client(self):
        """获取 Tushare 客户端"""
        if self._tushare_client is None:
            try:
                from openclaw_alpha.data_sources.tushare import TushareDataSource
                from openclaw_alpha.core.registry import DataSourceRegistry

                registry = DataSourceRegistry()
                data_source = registry.get_data_source("tushare")
                if data_source and data_source.is_available()[0]:
                    self._tushare_client = data_source.get_client()
            except Exception as e:
                logger.error(f"获取 Tushare 客户端失败: {e}")

        return self._tushare_client

    async def _refresh_stock_cache(self, client) -> None:
        """刷新 A 股缓存"""
        try:
            # 调用 Tushare API 获取股票列表
            df = await asyncio.to_thread(client.stock_basic, exchange="", list_status="L")

            codes_dict = {}
            for _, row in df.iterrows():
                ts_code = row["ts_code"]
                code = ts_code.split(".")[0]
                market = ts_code.split(".")[1] if "." in ts_code else ""
                codes_dict[code] = {"market": market, "name": row.get("name", "")}

            self._codes_cache["stock"] = codes_dict
            self._cache.save(self.name, "stock", codes_dict)
            logger.info(f"已刷新 A 股缓存，共 {len(codes_dict)} 只股票")

        except Exception as e:
            logger.error(f"刷新 A 股缓存失败: {e}")

    async def _refresh_index_cache(self, client) -> None:
        """刷新指数缓存"""
        try:
            df = await asyncio.to_thread(client.index_basic)

            codes_dict = {}
            for _, row in df.iterrows():
                ts_code = row["ts_code"]
                code = ts_code.split(".")[0]
                market = ts_code.split(".")[1] if "." in ts_code else ""
                codes_dict[code] = {"market": market, "name": row.get("name", "")}

            self._codes_cache["index"] = codes_dict
            self._cache.save(self.name, "index", codes_dict)
            logger.info(f"已刷新指数缓存，共 {len(codes_dict)} 只指数")

        except Exception as e:
            logger.error(f"刷新指数缓存失败: {e}")

    async def _refresh_etf_cache(self, client) -> None:
        """刷新 ETF 缓存"""
        try:
            df = await asyncio.to_thread(client.fund_basic, fund_type="ETF")

            codes_dict = {}
            for _, row in df.iterrows():
                ts_code = row["ts_code"]
                code = ts_code.split(".")[0]
                market = ts_code.split(".")[1] if "." in ts_code else ""
                codes_dict[code] = {"market": market, "name": row.get("name", "")}

            self._codes_cache["etf"] = codes_dict
            self._cache.save(self.name, "etf", codes_dict)
            logger.info(f"已刷新 ETF 缓存，共 {len(codes_dict)} 只 ETF")

        except Exception as e:
            logger.error(f"刷新 ETF 缓存失败: {e}")
