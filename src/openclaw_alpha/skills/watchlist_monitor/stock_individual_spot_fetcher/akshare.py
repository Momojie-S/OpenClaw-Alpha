# -*- coding: utf-8 -*-
"""个股实时行情 Fetcher - AKShare 实现"""

import asyncio
import logging
from typing import Any

import akshare as ak
import pandas as pd

from openclaw_alpha.core.code_converter import convert_code
from openclaw_alpha.core.data_source import DataSource
from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.skills.stock_screener.stock_spot_fetcher import StockSpot

logger = logging.getLogger(__name__)


class AkshareIndividualDataSource(DataSource):
    """AKShare 个股数据源"""

    name = "akshare_individual"
    required_config = []  # AKShare 无需配置

    def is_available(self) -> tuple[bool, str | None]:
        """检查数据源是否可用

        Returns:
            (True, None) - AKShare 个股接口无需认证
        """
        return True, None

    def get_client(self) -> Any:
        """获取客户端（AKShare 无客户端概念）"""
        return ak

    def close(self) -> None:
        """清理资源"""
        pass


class StockIndividualSpotFetcherAkshare(FetchMethod):
    """个股实时行情 Fetcher - AKShare 实现

    使用 ak.stock_individual_spot_xq() 获取个股实时行情。
    """

    name = "stock_individual_spot_akshare"
    required_data_source = "akshare_individual"
    priority = 10

    def __init__(self) -> None:
        """初始化"""
        super().__init__()
        self._data_source = AkshareIndividualDataSource()

    def is_available(self) -> tuple[bool, str | None]:
        """检查实现是否可用

        Returns:
            (是否可用, 错误信息)
        """
        return self._data_source.is_available()

    def _to_xueqiu_code(self, code: str) -> str:
        """将 6 位代码转换为雪球格式

        Args:
            code: 6 位股票代码（如 "000001"）

        Returns:
            雪球格式代码（如 "SZ000001"）

        Examples:
            >>> self._to_xueqiu_code("000001")
            "SZ000001"
            >>> self._to_xueqiu_code("600000")
            "SH600000"
        """
        # 标准化为 6 位
        code = code.zfill(6)

        # 判断市场
        if code.startswith(("60", "68")):
            # 上海交易所
            return f"SH{code}"
        elif code.startswith(("00", "30")):
            # 深圳交易所
            return f"SZ{code}"
        elif code.startswith(("4", "8")):
            # 北交所
            return f"BJ{code}"
        else:
            # 默认返回深圳
            return f"SZ{code}"

    async def fetch(self, codes: list[str]) -> list[StockSpot]:
        """获取指定股票的实时行情

        Args:
            codes: 股票代码列表（6位代码，如 ["000001", "600000"]）

        Returns:
            股票行情列表

        Raises:
            DataFetchError: 获取数据失败
        """
        if not codes:
            return []

        # 转换代码格式为雪球格式（如 "SH600000"）
        xueqiu_codes = [self._to_xueqiu_code(code) for code in codes]

        # 串行获取（AKShare 的同步接口）
        results = []
        for code, xq_code in zip(codes, xueqiu_codes):
            try:
                # 在线程池中运行同步函数
                df = await asyncio.get_event_loop().run_in_executor(
                    None, ak.stock_individual_spot_xq, xq_code
                )
                spot = self._parse_response(df, code)
                if spot:
                    results.append(spot)
            except Exception as e:
                logger.warning(f"获取 {code} 行情失败: {e}")
                # 继续处理下一只股票

        return results

    def _parse_response(self, df: pd.DataFrame, code: str) -> StockSpot | None:
        """解析 API 响应

        Args:
            df: API 返回的 DataFrame（item-value 格式）
            code: 股票代码

        Returns:
            StockSpot 对象，解析失败返回 None
        """
        try:
            # 将 DataFrame 转换为字典（item -> value）
            data = dict(zip(df["item"], df["value"]))

            # 提取字段
            name = str(data.get("名称", ""))

            # 涨幅（需要转换为浮点数）
            change_pct = self._safe_float(data.get("涨幅", 0))

            # 周转率（换手率）
            turnover_rate = self._safe_float(data.get("周转率", 0))

            # 成交额（需要转换为亿元）
            amount_raw = self._safe_float(data.get("成交额", 0))
            amount = amount_raw / 1e8  # 转换为亿元

            # 现价
            price = self._safe_float(data.get("现价", 0))

            # 总市值（使用流通值近似）
            market_cap_raw = self._safe_float(data.get("流通值", 0))
            market_cap = market_cap_raw / 1e8  # 转换为亿元

            return StockSpot(
                code=code,
                name=name,
                change_pct=change_pct,
                turnover_rate=turnover_rate,
                amount=amount,
                price=price,
                market_cap=market_cap,
            )
        except Exception as e:
            logger.error(f"解析 {code} 行情数据失败: {e}")
            return None

    def _safe_float(self, value: Any) -> float:
        """安全转换为浮点数

        Args:
            value: 原始值

        Returns:
            浮点数，转换失败返回 0
        """
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
