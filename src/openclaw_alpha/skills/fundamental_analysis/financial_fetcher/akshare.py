# -*- coding: utf-8 -*-
"""FinancialFetcher AKShare 实现"""

import logging

import akshare as ak
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.exceptions import DataSourceUnavailableError
from .models import FinancialData

logger = logging.getLogger(__name__)


class FinancialFetcherAkshare(FetchMethod):
    """FinancialFetcher AKShare 实现

    使用 AKShare 的 stock_financial_analysis_indicator_em 接口获取财务分析指标。
    """

    name = "financial_akshare"
    required_data_source = "akshare"
    priority = 10

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _call_api(self, code: str) -> pd.DataFrame:
        """调用 AKShare API 获取财务指标

        Args:
            code: 股票代码（如 "000001"）

        Returns:
            原始财务指标 DataFrame

        Raises:
            DataSourceUnavailableError: API 调用失败
        """
        try:
            # AKShare 需要带后缀的代码（如 000001.SZ）
            # 根据代码判断市场
            if code.startswith("6"):
                symbol = f"{code}.SH"
            else:
                symbol = f"{code}.SZ"

            df = ak.stock_financial_analysis_indicator_em(
                symbol=symbol, indicator="按报告期"
            )

            if df is None or df.empty:
                logger.warning(f"股票 {code} 无财务数据")
                return pd.DataFrame()

            return df

        except Exception as e:
            logger.error(f"获取股票 {code} 财务数据失败: {e}")
            raise DataSourceUnavailableError(
                data_source_name="akshare",
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

        # 字段映射（AKShare 字段 -> FinancialData 字段）
        field_map = {
            "SECURITY_NAME_ABBR": "name",
            "REPORT_DATE": "report_date",
            "ROEJQ": "roe",
            "EPSJB": "eps",
            "BPS": "bps",
            "XSJLL": "net_profit_margin",
            "XSMLL": "gross_profit_margin",
            "YYZSRGDHBZC": "revenue_growth",
            "NETPROFITRPHBZC": "profit_growth",
            "ZCFZL": "debt_ratio",
            "LD": "current_ratio",
            "SD": "quick_ratio",
            "MGJYXJJE": "cash_per_share",
        }

        # 构建数据字典
        data = {"code": code}

        for ak_field, model_field in field_map.items():
            value = row.get(ak_field)
            # 转换 NaN 为 None
            if pd.isna(value):
                data[model_field] = None
            else:
                data[model_field] = value

        # 处理日期格式
        if data.get("report_date"):
            # pandas Timestamp 转字符串
            data["report_date"] = str(data["report_date"])[:10]

        return FinancialData(**data)

    async def fetch(self, code: str) -> FinancialData:
        """获取财务分析指标

        Args:
            code: 股票代码

        Returns:
            财务指标数据
        """
        df = await self._call_api(code)
        return self._transform(df, code)
