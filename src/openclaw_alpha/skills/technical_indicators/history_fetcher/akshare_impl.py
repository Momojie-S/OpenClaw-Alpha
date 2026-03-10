# -*- coding: utf-8 -*-
"""AKShare 历史行情实现"""

from datetime import datetime, timedelta

import pandas as pd
from openclaw_alpha.core.fetcher import FetchMethod

from openclaw_alpha.data_sources import registry  # noqa: F401


class HistoryFetcherAkshare(FetchMethod):
    """AKShare 历史行情实现

    使用 ak.stock_zh_a_hist 接口获取日线历史行情数据。
    """

    name = "history_akshare"
    required_data_source = "akshare"
    priority = 10

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
        import akshare as ak

        # 计算日期范围
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")

        if not start_date:
            start_date = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")

        # 获取数据
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",  # 前复权
        )

        if df.empty:
            return df

        # 重命名列为英文
        df = df.rename(
            columns={
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "振幅": "amplitude",
                "涨跌幅": "change_pct",
                "涨跌额": "change",
                "换手率": "turnover",
            }
        )

        # 只返回最近 N 天
        if len(df) > days:
            df = df.tail(days)

        return df.reset_index(drop=True)
