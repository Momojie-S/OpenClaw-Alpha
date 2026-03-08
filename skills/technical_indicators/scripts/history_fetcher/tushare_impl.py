# -*- coding: utf-8 -*-
"""Tushare 历史行情实现"""

from datetime import datetime, timedelta

import pandas as pd
from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.data_sources import registry


class HistoryFetcherTushare(FetchMethod):
    """Tushare 历史行情实现

    使用 pro.daily 接口获取日线历史行情数据。
    """

    name = "history_tushare"
    required_data_source = "tushare"
    priority = 20  # 优先级高于 AKShare

    async def fetch(
        self, symbol: str, start_date: str = None, end_date: str = None, days: int = 60
    ) -> pd.DataFrame:
        """获取历史行情数据

        Args:
            symbol: 股票代码（如 "000001"）
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）
            days: 天数（默认 60 天）

        Returns:
            DataFrame: 历史行情数据，列名已转换为英文
        """
        # 获取 Tushare 客户端
        tushare_ds = registry.get("tushare")
        pro = await tushare_ds.get_client()

        # 计算日期范围
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")

        if not start_date:
            start_date = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")

        # 转换股票代码格式：000001 -> 000001.SZ
        ts_code = self._convert_code(symbol)

        # 获取数据
        df = pro.daily(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
        )

        if df.empty:
            return df

        # 重命名列
        df = df.rename(
            columns={
                "trade_date": "date",
                "vol": "volume",
                "pct_chg": "change_pct",
            }
        )

        # 只保留需要的列
        columns = ["date", "open", "high", "low", "close", "volume", "amount", "change_pct"]
        df = df[[c for c in columns if c in df.columns]]

        # 按日期排序
        df = df.sort_values("date")

        # 只返回最近 N 天
        if len(df) > days:
            df = df.tail(days)

        return df.reset_index(drop=True)

    def _convert_code(self, symbol: str) -> str:
        """转换股票代码格式

        Args:
            symbol: 6 位股票代码（如 "000001"）

        Returns:
            Tushare 格式代码（如 "000001.SZ"）
        """
        if "." in symbol:
            return symbol

        # 根据代码前缀判断市场
        if symbol.startswith(("60", "68")):
            return f"{symbol}.SH"
        elif symbol.startswith(("00", "30")):
            return f"{symbol}.SZ"
        elif symbol.startswith(("688", "689")):
            return f"{symbol}.SH"
        else:
            # 默认深圳
            return f"{symbol}.SZ"
