# -*- coding: utf-8 -*-
"""ValuationFetcher Tushare 实现"""

import logging
from datetime import datetime, timedelta
from typing import List

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.exceptions import DataSourceUnavailableError
from .models import ValuationData

logger = logging.getLogger(__name__)


# 指标映射（内部标识 -> Tushare 字段）
INDICATOR_MAP = {
    "pe_ttm": "pe_ttm",
    "pe_static": "pe",
    "pb": "pb",
    "market_cap": "total_mv",
    "pcf": "ps",  # Tushare 无市现率，用市销率替代
}

# period 映射（描述 -> 天数）
PERIOD_MAP = {
    "近一年": 365,
    "近半年": 180,
    "近三月": 90,
    "近一月": 30,
}


class ValuationFetcherTushare(FetchMethod):
    """ValuationFetcher Tushare 实现

    使用 Tushare 的 daily_basic 接口获取估值数据。

    积分要求：2000
    """

    name = "valuation_tushare"
    required_data_source = "tushare"
    required_credit = 2000
    priority = 20  # 优先于 AKShare

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _call_api(
        self, code: str, indicator: str, period: str
    ) -> pd.DataFrame:
        """调用 Tushare API 获取估值数据

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
        ts_field = INDICATOR_MAP.get(indicator)
        if not ts_field:
            raise DataSourceUnavailableError(
                data_source_name="tushare",
                reason=f"不支持的估值指标: {indicator}"
            )

        # 计算日期范围
        days = PERIOD_MAP.get(period, 365)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 格式化日期
        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")

        # 构造 ts_code（Tushare 格式：000001.SZ）
        # 假设 A 股代码为 6 位数字
        if code.startswith("6"):
            ts_code = f"{code}.SH"
        else:
            ts_code = f"{code}.SZ"

        try:
            client = await self.get_client()
            df = client.daily_basic(
                ts_code=ts_code,
                start_date=start_date_str,
                end_date=end_date_str,
                fields=f"trade_date,{ts_field}",
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
                data_source_name="tushare",
                reason=f"API 调用失败: {e}"
            ) from e

    def _transform(self, df: pd.DataFrame, indicator: str) -> List[ValuationData]:
        """转换原始数据为 ValuationData 列表

        Args:
            df: 原始估值数据 DataFrame
            indicator: 指标类型

        Returns:
            估值时间序列数据列表
        """
        if df.empty:
            return []

        ts_field = INDICATOR_MAP.get(indicator)
        result = []

        for _, row in df.iterrows():
            date = str(row["trade_date"])
            value = row.get(ts_field)

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
        return self._transform(df, indicator)
