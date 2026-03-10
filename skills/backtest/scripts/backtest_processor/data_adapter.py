# -*- coding: utf-8 -*-
"""数据转换模块 - 将 Fetcher 数据转换为 Backtrader 格式"""

from datetime import datetime

import backtrader as bt
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from skills.technical_indicators.scripts.history_fetcher import fetch as fetch_history


class DataAdapter:
    """数据转换器：Fetcher → Backtrader PandasData"""
    
    async def fetch_stock_data(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        days: int = 365,
    ) -> pd.DataFrame:
        """
        获取股票历史数据
        
        Args:
            stock_code: 股票代码（如 000001）
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            days: 天数（当 start_date/end_date 未提供时使用）
        
        Returns:
            股票历史数据 DataFrame
        
        Raises:
            RuntimeError: 数据获取失败
        """
        # 转换日期格式
        start_dt = start_date.replace("-", "") if start_date else None
        end_dt = end_date.replace("-", "") if end_date else None
        
        # 调用 history_fetcher（自动选择 Tushare/AKShare）
        try:
            df = await fetch_history(
                symbol=stock_code,
                start_date=start_dt,
                end_date=end_dt,
                days=days,
            )
        except Exception as e:
            raise RuntimeError(
                f"连接数据源 API 超时或失败。请检查网络连接后重试。"
                f"详细信息：获取股票 {stock_code} 历史数据时发生错误"
            ) from e

        if df is None or df.empty:
            raise RuntimeError(
                f"股票 {stock_code} 在 {start_date} ~ {end_date} 期间无数据。"
                f"请检查股票代码是否正确，或该时间段是否为非交易期"
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
            raise ValueError(
                f"股票 {stock_code} 数据为空。"
                f"请检查股票代码是否正确，或先获取该股票的历史数据"
            )

        # 选择需要的列（history_fetcher 已转为英文列名）
        required_cols = ["date", "open", "close", "high", "low", "volume"]

        # 检查必需列
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(
                    f"数据格式错误：缺少必需列 '{col}'。"
                    f"这是数据源返回的数据格式异常，请联系开发者并提供：股票代码={stock_code}、缺失列={col}"
                )
        
        # 创建副本并选择列
        data = df[required_cols].copy()
        
        # 转换日期格式
        data["date"] = pd.to_datetime(data["date"])
        data.set_index("date", inplace=True)
        
        # 创建 Backtrader 数据源
        data_feed = bt.feeds.PandasData(
            dataname=data,
            name=stock_code,
            fromdate=datetime.strptime(str(data.index[0]), "%Y-%m-%d %H:%M:%S"),
            todate=datetime.strptime(str(data.index[-1]), "%Y-%m-%d %H:%M:%S"),
            timeframe=bt.TimeFrame.Days
        )
        
        return data_feed


async def get_backtrader_data(
    stock_code: str,
    start_date: str,
    end_date: str,
    days: int = 365,
) -> bt.feeds.PandasData:
    """
    便捷函数：获取 Backtrader 格式的股票数据
    
    Args:
        stock_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        days: 天数
    
    Returns:
        Backtrader 数据源
    """
    adapter = DataAdapter()
    df = await adapter.fetch_stock_data(stock_code, start_date, end_date, days)
    return adapter.transform_to_backtrader(df, stock_code)
