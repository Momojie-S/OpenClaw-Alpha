# -*- coding: utf-8 -*-
"""业绩预告 Fetcher - Tushare 实现"""

import logging
from typing import Any

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.exceptions import DataSourceUnavailableError

logger = logging.getLogger(__name__)


class ForecastFetcherTushare(FetchMethod):
    """业绩预告数据获取器 - Tushare 实现

    使用 Tushare 的 forecast 接口获取业绩预告数据。

    积分要求：2000
    """

    name = "forecast_tushare"
    required_data_source = "tushare"
    required_credit = 2000
    priority = 20  # 优先于 AKShare

    # 风险等级映射
    RISK_LEVELS = {
        "首亏": "高",
        "预减": "高",
        "增亏": "高",
        "续亏": "高",
        "不确定": "中",
        "略减": "中",
        "预增": "无",
        "略增": "无",
        "扭亏": "无",
        "减亏": "无",
        "续盈": "无",
    }

    async def fetch(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """
        获取业绩预告数据

        Args:
            params: 参数字典
                - date: 日期，格式 YYYY-MM-DD（可选）
                - ts_code: 股票代码（可选）
                - period: 报告期（可选）

        Returns:
            业绩预告列表
        """
        df = await self._call_api(params)
        return self._transform(df)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    async def _call_api(self, params: dict[str, Any]) -> pd.DataFrame:
        """调用 Tushare API

        Args:
            params: 参数字典

        Returns:
            原始 DataFrame

        Raises:
            DataSourceUnavailableError: API 调用失败
        """
        try:
            client = await self.get_client()

            # 构造请求参数
            api_params = {}
            if params.get("ts_code"):
                # 将 6 位股票代码转换为 Tushare 格式（带后缀）
                ts_code = params["ts_code"]
                if len(ts_code) == 6:
                    # 判断市场
                    if ts_code.startswith(("6",)):
                        ts_code = f"{ts_code}.SH"
                    else:
                        ts_code = f"{ts_code}.SZ"
                api_params["ts_code"] = ts_code
            if params.get("period"):
                api_params["period"] = params["period"].replace("-", "")
            if params.get("date"):
                # 将日期格式转换为 YYYYMMDD
                api_params["ann_date"] = params["date"].replace("-", "")

            df = client.forecast(**api_params)

            if df is None or df.empty:
                logger.warning("无业绩预告数据")
                return pd.DataFrame()

            return df

        except Exception as e:
            logger.error(f"获取业绩预告数据失败: {e}")
            raise DataSourceUnavailableError(
                data_source_name="tushare",
                reason=f"API 调用失败: {e}"
            ) from e

    def _transform(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """
        转换数据格式

        Args:
            df: Tushare 返回的 DataFrame

        Returns:
            转换后的列表
        """
        if df.empty:
            return []

        records = []

        for _, row in df.iterrows():
            # 处理日期格式
            ann_date = str(row.get("ann_date", ""))
            if ann_date:
                ann_date = f"{ann_date[:4]}-{ann_date[4:6]}-{ann_date[6:8]}"

            record = {
                "code": str(row.get("ts_code", ""))[:6],  # 去掉后缀
                "name": str(row.get("name", "")),
                "indicator": "",  # Tushare 可能没有这个字段
                "change_desc": str(row.get("change_reason", "")),
                "forecast_value": row.get("net_profit_min"),  # 预测净利润下限
                "change_pct": row.get("p_change_min"),  # 变动幅度下限
                "change_reason": str(row.get("change_reason", "")),
                "forecast_type": str(row.get("type", "")),
                "last_year_value": row.get("last_parent_net"),  # 上年同期
                "announce_date": ann_date,
                "risk_level": self.RISK_LEVELS.get(str(row.get("type", "")), "未知"),
            }
            records.append(record)

        return records
