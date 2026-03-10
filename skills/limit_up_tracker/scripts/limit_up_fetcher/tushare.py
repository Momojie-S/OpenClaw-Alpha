# -*- coding: utf-8 -*-
"""涨停追踪 Fetcher - Tushare 实现"""

import logging
from typing import Optional

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.exceptions import DataSourceUnavailableError
from .models import LimitUpItem, LimitUpResult, LimitUpType

logger = logging.getLogger(__name__)


class LimitUpFetcherTushare(FetchMethod):
    """涨停追踪 Fetcher - Tushare 实现

    使用 Tushare 的 limit_list_d 接口获取涨跌停数据。

    积分要求：5000
    """

    name = "limit_up_tushare"
    required_data_source = "tushare"
    required_credit = 5000
    priority = 20

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    async def _call_api(
        self,
        trade_date: str,
        limit_type: LimitUpType = LimitUpType.LIMIT_UP,
    ) -> pd.DataFrame:
        """调用 Tushare API

        Args:
            trade_date: 交易日期 (YYYYMMDD)
            limit_type: 涨停类型

        Returns:
            原始 DataFrame
        """
        try:
            client = await self.get_client()

            # 根据类型设置参数
            if limit_type == LimitUpType.LIMIT_UP:
                up_lim = "U"  # 涨停
            elif limit_type == LimitUpType.LIMIT_DOWN:
                up_lim = "D"  # 跌停
            else:
                up_lim = "U"  # 默认涨停

            df = client.limit_list_d(trade_date=trade_date, limit=up_lim)

            if df is None or df.empty:
                logger.warning(f"无涨跌停数据 (date={trade_date})")
                return pd.DataFrame()

            return df

        except Exception as e:
            logger.error(f"获取涨跌停数据失败: {e}")
            raise DataSourceUnavailableError(
                data_source_name="tushare",
                reason=f"API 调用失败: {e}"
            ) from e

    def _transform(
        self,
        df: pd.DataFrame,
        date: str,
        limit_type: LimitUpType,
    ) -> LimitUpResult:
        """转换数据格式"""
        if df.empty:
            return LimitUpResult(
                date=date,
                limit_type=limit_type,
                total=0,
                items=[],
                continuous_stat={},
            )

        items = []
        for _, row in df.iterrows():
            # 解析连板数
            up_stat = str(row.get("up_stat", ""))
            continuous = 1
            if up_stat:
                # 格式如 "2/3" 表示 2 连板 / 3 次涨停
                parts = up_stat.split("/")
                if parts:
                    try:
                        continuous = int(parts[0])
                    except ValueError:
                        continuous = 1

            item = LimitUpItem(
                code=str(row.get("ts_code", ""))[:6],
                name=str(row.get("name", "")),
                change_pct=float(row.get("pct_chg", 0)),
                price=float(row.get("close", 0)),
                amount=float(row.get("amount", 0)) / 100000000 if row.get("amount") else 0,  # 千元 -> 亿元
                float_mv=float(row.get("float_mv", 0)) / 100000000 if row.get("float_mv") else 0,  # 元 -> 亿元
                total_mv=float(row.get("total_mv", 0)) / 100000000 if row.get("total_mv") else 0,  # 元 -> 亿元
                turnover_rate=float(row.get("turnover_rate", 0)) if row.get("turnover_rate") else 0,
                first_limit_time="",  # Tushare 不提供
                last_limit_time="",   # Tushare 不提供
                limit_times=0,        # Tushare 不提供
                limit_stat=up_stat,
                continuous=continuous,
                industry=str(row.get("industry", "")),
            )
            items.append(item)

        return LimitUpResult(
            date=date,
            limit_type=limit_type,
            total=len(items),
            items=items,
            continuous_stat={},  # 由入口类计算
        )

    async def fetch(
        self,
        date: str,
        limit_type: LimitUpType = LimitUpType.LIMIT_UP,
    ) -> LimitUpResult:
        """获取涨停数据

        Args:
            date: 交易日期 (YYYYMMDD)
            limit_type: 涨停类型

        Returns:
            LimitUpResult
        """
        df = await self._call_api(date, limit_type)
        return self._transform(df, date, limit_type)
