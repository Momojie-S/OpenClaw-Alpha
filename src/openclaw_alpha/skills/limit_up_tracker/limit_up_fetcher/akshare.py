# -*- coding: utf-8 -*-
"""涨停追踪 Fetcher - AKShare 实现"""

import akshare as ak
import pandas as pd

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.exceptions import RetryableError

from .models import LimitUpItem, LimitUpType


class LimitUpFetcherAkshare(FetchMethod):
    """涨停追踪 Fetcher - AKShare 实现"""

    name = "limit_up_akshare"
    required_data_source = "akshare"
    priority = 10

    async def fetch(self, date: str, limit_type: LimitUpType):
        """
        获取涨停数据

        Args:
            date: 交易日期 (YYYYMMDD)
            limit_type: 涨停类型

        Returns:
            LimitUpResult
        """
        from .models import LimitUpResult

        try:
            df = await self._call_api(date, limit_type)
            items = self._transform(df, limit_type)

            return LimitUpResult(
                date=date,
                limit_type=limit_type,
                items=items,
                total=len(items),
                continuous_stat={},
            )
        except Exception as e:
            raise RetryableError(f"AKShare API error: {e}") from e

    async def _call_api(self, date: str, limit_type: LimitUpType) -> pd.DataFrame:
        """调用 AKShare API"""
        if limit_type == LimitUpType.LIMIT_UP:
            return ak.stock_zt_pool_em(date=date)
        elif limit_type == LimitUpType.LIMIT_DOWN:
            return ak.stock_zt_pool_dtgc_em(date=date)
        elif limit_type == LimitUpType.BROKEN:
            return ak.stock_zt_pool_zbgc_em(date=date)
        elif limit_type == LimitUpType.PREVIOUS:
            return ak.stock_zt_pool_previous_em(date=date)
        else:
            raise ValueError(
                f"参数 limit_type 值无效（收到 '{limit_type}'）。"
                f"可用类型：LimitUpType.LIMIT_UP（涨停）、LimitUpType.LIMIT_DOWN（跌停）、"
                f"LimitUpType.BROKEN（炸板）、LimitUpType.PREVIOUS（昨日涨停）"
            )

    def _transform(self, df: pd.DataFrame, limit_type: LimitUpType) -> list[LimitUpItem]:
        """转换数据"""
        if df.empty:
            return []

        items = []

        # 根据类型选择字段映射
        if limit_type == LimitUpType.PREVIOUS:
            # 昨日涨停的字段略有不同
            for _, row in df.iterrows():
                item = LimitUpItem(
                    code=str(row.get("代码", "")),
                    name=str(row.get("名称", "")),
                    change_pct=float(row.get("涨跌幅", 0)),
                    price=float(row.get("最新价", 0)),
                    amount=float(row.get("成交额", 0)) / 1e8,  # 转为亿
                    float_mv=float(row.get("流通市值", 0)) / 1e8,
                    total_mv=float(row.get("总市值", 0)) / 1e8,
                    turnover_rate=float(row.get("换手率", 0)),
                    first_limit_time=str(row.get("昨日封板时间", "")),
                    last_limit_time="",
                    limit_times=0,
                    limit_stat=str(row.get("涨停统计", "")),
                    continuous=int(row.get("昨日连板数", 1)),
                    industry=str(row.get("所属行业", "")),
                )
                items.append(item)
        elif limit_type == LimitUpType.BROKEN:
            # 炸板股池字段
            for _, row in df.iterrows():
                item = LimitUpItem(
                    code=str(row.get("代码", "")),
                    name=str(row.get("名称", "")),
                    change_pct=float(row.get("涨跌幅", 0)),
                    price=float(row.get("最新价", 0)),
                    amount=float(row.get("成交额", 0)) / 1e8,
                    float_mv=float(row.get("流通市值", 0)) / 1e8,
                    total_mv=float(row.get("总市值", 0)) / 1e8,
                    turnover_rate=float(row.get("换手率", 0)),
                    first_limit_time=str(row.get("首次封板时间", "")),
                    last_limit_time="",
                    limit_times=int(row.get("炸板次数", 0)),
                    limit_stat=str(row.get("涨停统计", "")),
                    continuous=0,  # 炸板股没有连板概念
                    industry=str(row.get("所属行业", "")),
                )
                items.append(item)
        else:
            # 涨停/跌停
            for _, row in df.iterrows():
                # 跌停使用"连续跌停"字段，涨停使用"连板数"字段
                if limit_type == LimitUpType.LIMIT_DOWN:
                    continuous_val = int(row.get("连续跌停", 1))
                else:
                    continuous_val = int(row.get("连板数", 1))

                item = LimitUpItem(
                    code=str(row.get("代码", "")),
                    name=str(row.get("名称", "")),
                    change_pct=float(row.get("涨跌幅", 0)),
                    price=float(row.get("最新价", 0)),
                    amount=float(row.get("成交额", 0)) / 1e8,
                    float_mv=float(row.get("流通市值", 0)) / 1e8,
                    total_mv=float(row.get("总市值", 0)) / 1e8,
                    turnover_rate=float(row.get("换手率", 0)),
                    first_limit_time=str(row.get("首次封板时间", "")),
                    last_limit_time=str(row.get("最后封板时间", "")),
                    limit_times=int(row.get("炸板次数", 0) if limit_type == LimitUpType.LIMIT_UP else row.get("开板次数", 0)),
                    limit_stat=str(row.get("涨停统计", "") if limit_type == LimitUpType.LIMIT_UP else f"{continuous_val}连跌"),
                    continuous=continuous_val,
                    industry=str(row.get("所属行业", "")),
                )
                items.append(item)

        return items
