# -*- coding: utf-8 -*-
"""ValuationFetcher AKShare 实现"""

import logging
from typing import List

import akshare as ak
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.exceptions import DataSourceUnavailableError
from .models import ValuationData

logger = logging.getLogger(__name__)


# 指标映射（内部标识 -> AKShare 参数）
INDICATOR_MAP = {
    "pe_ttm": "市盈率(TTM)",
    "pe_static": "市盈率(静)",
    "pb": "市净率",
    "market_cap": "总市值",
    "pcf": "市现率",
}


class ValuationFetcherAkshare(FetchMethod):
    """ValuationFetcher AKShare 实现

    使用 AKShare 的 stock_zh_valuation_baidu 接口获取估值数据。
    """

    name = "valuation_akshare"
    required_data_source = "akshare"
    priority = 10

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _call_api(
        self, code: str, indicator: str, period: str
    ) -> pd.DataFrame:
        """调用 AKShare API 获取估值数据

        Args:
            code: 股票代码（如 "000001"）
            indicator: 指标类型（内部标识）
            period: 时间范围

        Returns:
            原始估值数据 DataFrame

        Raises:
            DataSourceUnavailableError: API 调用失败或指标不存在
        """
        # 转换指标标识
        ak_indicator = INDICATOR_MAP.get(indicator)
        if not ak_indicator:
            raise DataSourceUnavailableError(
                data_source_name="akshare",
                reason=f"不支持的估值指标: {indicator}"
            )

        try:
            df = ak.stock_zh_valuation_baidu(
                symbol=code, indicator=ak_indicator, period=period
            )

            if df is None or df.empty:
                logger.warning(
                    f"股票 {code} 无估值数据 (indicator={indicator})"
                )
                return pd.DataFrame()

            return df

        except Exception as e:
            logger.error(f"获取股票 {code} 估值数据失败: {e}")
            raise DataSourceUnavailableError(
                data_source_name="akshare",
                reason=f"API 调用失败: {e}"
            ) from e

    def _transform(self, df: pd.DataFrame) -> List[ValuationData]:
        """转换原始数据为 ValuationData 列表

        Args:
            df: 原始估值数据 DataFrame

        Returns:
            估值时间序列数据列表
        """
        if df.empty:
            return []

        result = []
        for _, row in df.iterrows():
            date = str(row["date"])
            value = row["value"]

            # 跳过 NaN
            if pd.isna(value):
                continue

            result.append(ValuationData(date=date, value=float(value)))

        return result

    async def fetch(
        self, code: str, indicator: str, period: str = "近一年"
    ) -> List[ValuationData]:
        """获取估值数据

        Args:
            code: 股票代码
            indicator: 指标类型
            period: 时间范围

        Returns:
            估值时间序列数据列表
        """
        df = await self._call_api(code, indicator, period)
        return self._transform(df)
