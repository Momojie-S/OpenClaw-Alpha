# -*- coding: utf-8 -*-
"""数据转换模块 - 将 Fetcher 数据转换为 Backtrader 格式"""

from datetime import datetime
from typing import Optional

import akshare as ak
import backtrader as bt
import pandas as pd


class DataAdapter:
    """数据转换器：Fetcher → Backtrader PandasData"""
    
    def fetch_stock_data(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        adj: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取股票历史数据
        
        Args:
            stock_code: 股票代码（如 000001）
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            adj: 复权类型（qfq-前复权, hfq-后复权, None-不复权）
        
        Returns:
            股票历史数据 DataFrame
        
        Raises:
            RuntimeError: 数据获取失败
        """
        # 注意：AKShare 的日期格式为 YYYYMMDD
        start_dt = start_date.replace("-", "")
        end_dt = end_date.replace("-", "")
        
        # 调用 AKShare 接口
        try:
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_dt,
                end_date=end_dt,
                adjust=adj
            )
        except Exception as e:
            raise RuntimeError(
                f"获取股票 {stock_code} 历史数据失败: {e}"
            ) from e
        
        if df is None or df.empty:
            raise RuntimeError(
                f"股票 {stock_code} 在 {start_date} ~ {end_date} 期间无数据"
            )
        
        return df
    
    def transform_to_backtrader(
        self,
        df: pd.DataFrame,
        stock_code: str
    ) -> bt.feeds.PandasData:
        """
        将 DataFrame 转换为 Backtrader PandasData
        
        Args:
            df: 股票历史数据
            stock_code: 股票代码
        
        Returns:
            Backtrader 数据源
        """
        # 确保数据不为空
        if df is None or df.empty:
            raise ValueError(f"股票 {stock_code} 数据为空")
        
        # 重命名列（AKShare 列名 → Backtrader 标准列名）
        column_mapping = {
            "日期": "datetime",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "涨跌幅": "pct_change",
            "涨跌额": "change",
            "换手率": "turnover"
        }
        
        # 选择需要的列
        required_cols = ["日期", "开盘", "收盘", "最高", "最低", "成交量"]
        
        # 检查必需列
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"缺少必需列: {col}")
        
        # 创建副本并选择列
        data = df[required_cols].copy()
        data.columns = ["datetime", "open", "close", "high", "low", "volume"]
        
        # 转换日期格式
        data["datetime"] = pd.to_datetime(data["datetime"])
        data.set_index("datetime", inplace=True)
        
        # 创建 Backtrader 数据源
        data_feed = bt.feeds.PandasData(
            dataname=data,
            name=stock_code,
            fromdate=datetime.strptime(str(data.index[0]), "%Y-%m-%d %H:%M:%S"),
            todate=datetime.strptime(str(data.index[-1]), "%Y-%m-%d %H:%M:%S"),
            timeframe=bt.TimeFrame.Days
        )
        
        return data_feed


def get_backtrader_data(
    stock_code: str,
    start_date: str,
    end_date: str,
    adj: str = "qfq"
) -> bt.feeds.PandasData:
    """
    便捷函数：获取 Backtrader 格式的股票数据
    
    Args:
        stock_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        adj: 复权类型
    
    Returns:
        Backtrader 数据源
    """
    adapter = DataAdapter()
    df = adapter.fetch_stock_data(stock_code, start_date, end_date, adj)
    return adapter.transform_to_backtrader(df, stock_code)
