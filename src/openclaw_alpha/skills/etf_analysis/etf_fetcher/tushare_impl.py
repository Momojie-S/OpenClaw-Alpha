# -*- coding: utf-8 -*-
"""ETF 数据 Fetcher - Tushare 实现"""

import logging
from typing import Any, Optional

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.exceptions import DataSourceUnavailableError

logger = logging.getLogger(__name__)


class EtfFetcherTushare(FetchMethod):
    """ETF 数据获取器 - Tushare 实现

    使用 Tushare 的 fund_daily 接口获取 ETF 日线数据。

    积分要求：5000
    """

    name = "etf_tushare"
    required_data_source = "tushare"
    required_credit = 5000
    priority = 20  # 优先于 AKShare

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    async def _call_api(
        self,
        ts_code: Optional[str] = None,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """调用 Tushare API

        Args:
            ts_code: ETF 代码
            trade_date: 交易日期
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            原始 DataFrame
        """
        try:
            client = await self.get_client()

            params = {}
            if ts_code:
                params["ts_code"] = ts_code
            if trade_date:
                params["trade_date"] = trade_date
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date

            df = client.fund_daily(**params)

            if df is None or df.empty:
                logger.warning("无 ETF 数据")
                return pd.DataFrame()

            return df

        except Exception as e:
            logger.error(f"获取 ETF 数据失败: {e}")
            raise DataSourceUnavailableError(
                data_source_name="tushare",
                reason=f"API 调用失败: {e}"
            ) from e

    def _transform(self, df: pd.DataFrame) -> list[dict]:
        """转换数据格式"""
        if df.empty:
            return []

        result = []
        for _, row in df.iterrows():
            trade_date = str(row.get("trade_date", ""))
            if trade_date:
                date_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
            else:
                date_str = ""

            result.append({
                "code": str(row.get("ts_code", ""))[:6],
                "name": "",  # Tushare fund_daily 不提供名称
                "date": date_str,
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "volume": float(row.get("vol", 0)),
                "amount": float(row.get("amount", 0)),
                "change_pct": float(row.get("pct_chg", 0)),
            })

        return result

    async def fetch(self, params: dict[str, Any]) -> list[dict]:
        """获取 ETF 数据

        注意：Tushare fund_daily API 要求至少填写 ts_code 或 trade_date 参数。
        对于获取全部 ETF 实时行情的场景，应该使用 AKShare 实现。
        """
        ts_code = params.get("ts_code")
        trade_date = params.get("trade_date")

        # 检查参数是否满足 API 要求
        if not ts_code and not trade_date:
            # 不满足 API 要求，让其他实现处理
            raise DataSourceUnavailableError(
                data_source_name="tushare",
                reason="fund_daily API 要求至少填写 ts_code 或 trade_date 参数，"
                       "获取全部 ETF 实时行情请使用 AKShare 实现",
            )

        df = await self._call_api(
            ts_code=ts_code,
            trade_date=trade_date,
            start_date=params.get("start_date"),
            end_date=params.get("end_date"),
        )
        return self._transform(df)
