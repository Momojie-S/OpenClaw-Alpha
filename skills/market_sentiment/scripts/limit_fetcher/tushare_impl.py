# -*- coding: utf-8 -*-
"""涨跌停数据获取器 - Tushare 实现"""

import logging
from typing import Optional

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.exceptions import DataSourceUnavailableError

logger = logging.getLogger(__name__)


class LimitFetcherTushare(FetchMethod):
    """涨跌停数据获取器 - Tushare 实现

    使用 Tushare 的 limit_list_d 接口获取涨跌停统计数据。

    积分要求：5000
    """

    name = "limit_tushare"
    required_data_source = "tushare"
    required_credit = 5000
    priority = 20

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    async def _call_api(self, trade_date: str) -> pd.DataFrame:
        """调用 Tushare API

        Args:
            trade_date: 交易日期 (YYYYMMDD)

        Returns:
            原始 DataFrame
        """
        try:
            client = await self.get_client()
            # 获取涨停和跌停数据
            df_up = client.limit_list_d(trade_date=trade_date, limit="U")
            df_down = client.limit_list_d(trade_date=trade_date, limit="D")

            return df_up, df_down

        except Exception as e:
            logger.error(f"获取涨跌停数据失败: {e}")
            raise DataSourceUnavailableError(
                data_source_name="tushare",
                reason=f"API 调用失败: {e}"
            ) from e

    def _transform(
        self,
        df_up: pd.DataFrame,
        df_down: pd.DataFrame,
        date: str,
    ) -> dict:
        """转换数据格式"""
        up_count = len(df_up) if df_up is not None and not df_up.empty else 0
        down_count = len(df_down) if df_down is not None and not df_down.empty else 0

        return {
            "date": date,
            "up_count": up_count,
            "down_count": down_count,
            "up_down_ratio": up_count / down_count if down_count > 0 else 0,
        }

    async def fetch(self, date: str) -> dict:
        """获取涨跌停统计数据

        Args:
            date: 交易日期 (YYYY-MM-DD)

        Returns:
            涨跌停统计数据
        """
        # 转换日期格式
        trade_date = date.replace("-", "")

        df_up, df_down = await self._call_api(trade_date)
        return self._transform(df_up, df_down, date)
