# -*- coding: utf-8 -*-
"""FinancialFetcher Tushare 实现"""

import logging

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.code_converter import convert_code
from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.exceptions import DataSourceUnavailableError
from .models import FinancialData

logger = logging.getLogger(__name__)


class FinancialFetcherTushare(FetchMethod):
    """FinancialFetcher Tushare 实现

    使用 Tushare 的 fina_indicator 接口获取财务分析指标。

    积分要求：2000
    """

    name = "financial_tushare"
    required_data_source = "tushare"
    required_credit = 2000
    priority = 20  # 优先于 AKShare

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _call_api(self, code: str) -> pd.DataFrame:
        """调用 Tushare API 获取财务指标

        Args:
            code: 股票代码（如 "000001"）

        Returns:
            原始财务指标 DataFrame

        Raises:
            DataSourceUnavailableError: API 调用失败
        """
        # 使用代码转换器转换为 Tushare 格式
        ts_code = convert_code(code, "tushare")

        try:
            client = await self.get_client()
            df = client.fina_indicator(ts_code=ts_code)

            if df is None or df.empty:
                logger.warning(f"股票 {code} 无财务数据")
                return pd.DataFrame()

            return df

        except Exception as e:
            logger.error(f"获取股票 {code} 财务数据失败: {e}")
            raise DataSourceUnavailableError(
                data_source_name="tushare",
                reason=f"API 调用失败: {e}"
            ) from e

    def _transform(self, df: pd.DataFrame, code: str) -> FinancialData:
        """转换原始数据为 FinancialData

        Args:
            df: 原始财务指标 DataFrame
            code: 股票代码

        Returns:
            财务指标数据
        """
        if df.empty:
            return FinancialData(code=code, name="", report_date="")

        # 取最新一期数据
        row = df.iloc[0]

        # 字段映射（Tushare 字段 -> FinancialData 字段）
        data = {
            "code": code,
            "name": "",  # Tushare 不提供名称，需要另外查询
            "report_date": str(row.get("end_date", ""))[:10],
            "roe": self._get_float(row, "roe_waa"),  # 加权 ROE
            "eps": self._get_float(row, "eps"),
            "bps": self._get_float(row, "bps"),
            "net_profit_margin": self._get_float(row, "netprofit_margin"),
            "gross_profit_margin": self._get_float(row, "grossprofit_margin"),
            "revenue_growth": self._get_float(row, "or_yoy"),
            "profit_growth": self._get_float(row, "netprofit_yoy"),
            "debt_ratio": self._get_float(row, "debt_to_assets"),
            "current_ratio": self._get_float(row, "current_ratio"),
            "quick_ratio": self._get_float(row, "quick_ratio"),
            "cash_per_share": self._get_float(row, "ocfps"),
        }

        return FinancialData(**data)

    def _get_float(self, row: pd.Series, field: str) -> float | None:
        """安全获取浮点值

        Args:
            row: 数据行
            field: 字段名

        Returns:
            浮点值或 None
        """
        value = row.get(field)
        if pd.isna(value):
            return None
        return float(value)

    async def fetch(self, code: str) -> FinancialData:
        """获取财务分析指标

        Args:
            code: 股票代码

        Returns:
            财务指标数据
        """
        df = await self._call_api(code)
        return self._transform(df, code)
