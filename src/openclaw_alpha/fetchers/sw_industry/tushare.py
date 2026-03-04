# -*- coding: utf-8 -*-
"""申万行业 Tushare 数据获取器"""

from datetime import datetime
from typing import Any

import pandas as pd

from openclaw_alpha.core.fetcher import DataFetcher
from openclaw_alpha.fetchers.sw_industry.models import (
    SwIndustryFetchParams,
    SwIndustryFetchResult,
    SwIndustryItem,
)


class SwIndustryTushareFetcher(
    DataFetcher[SwIndustryFetchParams, SwIndustryFetchResult]
):
    """申万行业 Tushare 数据获取器

    通过 Tushare Pro API 获取申万行业指数日行情数据。

    Attributes:
        name: Fetcher 标识
        data_type: 数据类型
        required_data_source: 需要的数据源
        priority: 优先级
    """

    name = "tushare_sw_industry"
    data_type = "sw_industry"
    required_data_source = "tushare"
    priority = 1

    async def fetch(self, params: SwIndustryFetchParams) -> SwIndustryFetchResult:
        """获取申万行业行情数据

        Args:
            params: 获取参数

        Returns:
            申万行业获取结果
        """
        import os

        import tushare as ts

        api_token = os.environ.get("TUSHARE_TOKEN")
        if not api_token:
            raise ValueError("TUSHARE_TOKEN 未配置")

        pro = ts.pro_api(api_token)

        # 处理日期参数
        trade_date = params.trade_date
        if trade_date is None:
            trade_date = datetime.now().strftime("%Y%m%d")

        # 调用 Tushare API 获取申万行业指数日行情
        df: pd.DataFrame = pro.sw_daily(trade_date=trade_date)

        if df is None or df.empty:
            return SwIndustryFetchResult(
                trade_date=trade_date,
                level=params.level,
                data_source="Tushare",
                items=[],
            )

        # 行业层级筛选
        df = self._filter_by_level(df, params.level)

        # 计算换手率
        df = self._calculate_turnover_rate(df)

        # 确定排序字段
        sort_column = self._get_sort_column(params.sort_by)

        # 按排序字段降序排列
        if sort_column in df.columns:
            df = df.sort_values(by=sort_column, ascending=False)

        # 取前 N 个
        df = df.head(params.top)

        # 构建结果数据
        items: list[SwIndustryItem] = []
        for idx, row in enumerate(df.itertuples(), start=1):
            item = self._parse_row(idx, row)
            items.append(item)

        return SwIndustryFetchResult(
            trade_date=trade_date,
            level=params.level,
            data_source="Tushare",
            items=items,
        )

    def _filter_by_level(self, df: pd.DataFrame, level: str) -> pd.DataFrame:
        """按行业层级筛选

        Args:
            df: 原始数据
            level: 行业层级

        Returns:
            筛选后的数据
        """
        if level == "L1":
            # 一级行业：代码以 801 开头
            df = df[df["ts_code"].str.startswith("801")]
        elif level == "L2":
            # 二级行业：代码以 801 开头
            df = df[df["ts_code"].str.startswith("801")]
        elif level == "L3":
            # 三级行业：代码以 85 开头
            df = df[df["ts_code"].str.startswith("85")]
        return df

    def _calculate_turnover_rate(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算换手率

        换手率 = 成交额 / 流通市值 * 100
        amount: 千元, float_mv: 万元

        Args:
            df: 原始数据

        Returns:
            添加换手率列后的数据
        """
        df = df.copy()
        df["turnover_rate"] = df.apply(
            lambda row: (row["amount"] * 1000) / (row["float_mv"] * 10000) * 100
            if pd.notna(row["float_mv"]) and row["float_mv"] > 0
            else 0,
            axis=1,
        )
        return df

    def _get_sort_column(self, sort_by: str) -> str:
        """获取排序字段名

        Args:
            sort_by: 排序字段参数

        Returns:
            DataFrame 中的列名
        """
        sort_field_map = {
            "change_pct": "pct_change",
            "amount": "amount",
            "turnover_rate": "turnover_rate",
        }
        return sort_field_map.get(sort_by, "pct_change")

    def _parse_row(self, rank: int, row: Any) -> SwIndustryItem:
        """解析数据行

        Args:
            rank: 排名
            row: 数据行

        Returns:
            申万行业数据项
        """
        volume = getattr(row, "vol", 0) or 0
        amount = getattr(row, "amount", 0) or 0

        return SwIndustryItem(
            rank=rank,
            board_code=str(getattr(row, "ts_code", "")),
            board_name=str(getattr(row, "name", "")),
            change_pct=round(float(getattr(row, "pct_change", 0) or 0), 2),
            close=round(float(getattr(row, "close", 0) or 0), 2),
            volume=round(float(volume) / 10000, 2),  # 手 -> 万手
            amount=round(float(amount) * 1000 / 100000000, 2),  # 千元 -> 亿元
            turnover_rate=round(float(getattr(row, "turnover_rate", 0) or 0), 2),
            float_mv=round(float(getattr(row, "float_mv", 0) or 0) / 10000, 2),  # 万元 -> 亿
            total_mv=round(float(getattr(row, "total_mv", 0) or 0) / 10000, 2),  # 万元 -> 亿
            pe=round(float(getattr(row, "pe", 0) or 0), 2),
            pb=round(float(getattr(row, "pb", 0) or 0), 2),
        )
