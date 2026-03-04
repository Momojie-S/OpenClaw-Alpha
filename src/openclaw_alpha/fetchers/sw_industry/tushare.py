# -*- coding: utf-8 -*-
"""申万行业 Tushare 数据获取器"""

import os
from datetime import datetime
from typing import Any

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.exceptions import (
    AuthenticationError,
    NetworkError,
    RateLimitError,
    ServerError,
    TimeoutError,
)
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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    def _call_api(self, trade_date: str) -> pd.DataFrame:
        """调用 Tushare API 获取申万行业指数日行情

        Args:
            trade_date: 交易日期 (YYYYMMDD)

        Returns:
            原始 API 响应 DataFrame

        Raises:
            AuthenticationError: 认证失败
            RateLimitError: 请求限流
            TimeoutError: 请求超时
            ServerError: 服务端错误
            NetworkError: 网络错误
        """
        import tushare as ts

        api_token = os.environ.get("TUSHARE_TOKEN")
        if not api_token:
            raise ValueError("TUSHARE_TOKEN 未配置")

        pro = ts.pro_api(api_token)

        try:
            df: pd.DataFrame = pro.sw_daily(trade_date=trade_date)
            return df
        except Exception as e:
            error_msg = str(e).lower()
            # 根据错误信息转换为对应异常
            if "token" in error_msg or "auth" in error_msg or "401" in error_msg:
                raise AuthenticationError(f"Tushare 认证失败: {e}") from e
            elif "429" in error_msg or "limit" in error_msg or "freq" in error_msg:
                raise RateLimitError(f"Tushare 请求限流: {e}") from e
            elif "timeout" in error_msg or "timed out" in error_msg:
                raise TimeoutError(f"Tushare 请求超时: {e}") from e
            elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                raise ServerError(f"Tushare 服务端错误: {e}") from e
            elif "connect" in error_msg or "network" in error_msg or "dns" in error_msg:
                raise NetworkError(f"Tushare 网络错误: {e}") from e
            else:
                # 其他异常不重试，直接抛出
                raise

    def _transform(
        self, df: pd.DataFrame, params: SwIndustryFetchParams
    ) -> list[SwIndustryItem]:
        """将原始 API 响应转换为业务模型

        Args:
            df: 原始 API 响应 DataFrame
            params: 获取参数

        Returns:
            申万行业列表
        """
        if df is None or df.empty:
            return []

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

        return items

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
            df = df[df["ts_code"].str.startswith("801")]  # type: ignore[assignment]
        elif level == "L2":
            # 二级行业：代码以 801 开头
            df = df[df["ts_code"].str.startswith("801")]  # type: ignore[assignment]
        elif level == "L3":
            # 三级行业：代码以 85 开头
            df = df[df["ts_code"].str.startswith("85")]  # type: ignore[assignment]
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

    async def fetch(self, params: SwIndustryFetchParams) -> SwIndustryFetchResult:
        """获取申万行业行情数据

        Args:
            params: 获取参数

        Returns:
            申万行业获取结果
        """
        # 处理日期参数
        trade_date = params.trade_date
        if trade_date is None:
            trade_date = datetime.now().strftime("%Y%m%d")

        # 调用 API 获取原始数据
        df = self._call_api(trade_date)

        # 转换数据
        items = self._transform(df, params)

        return SwIndustryFetchResult(
            trade_date=trade_date,
            level=params.level,
            data_source="Tushare",
            items=items,
        )


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        """调试入口"""
        fetcher = SwIndustryTushareFetcher()
        result = await fetcher.fetch(SwIndustryFetchParams(top=10))
        print(f"数据源: {result.data_source}")
        print(f"日期: {result.trade_date}")
        print(f"层级: {result.level}")
        print(f"数量: {len(result.items)}")
        for item in result.items[:5]:
            print(
                f"  {item.rank}. {item.board_name} ({item.board_code}) "
                f"涨跌幅: {item.change_pct}%"
            )

    asyncio.run(main())
