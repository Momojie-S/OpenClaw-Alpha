# -*- coding: utf-8 -*-
"""概念板块 AKShare 数据获取器"""

from datetime import datetime
from typing import Any

import akshare as ak
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.exceptions import (
    NetworkError,
    RateLimitError,
    ServerError,
    TimeoutError,
)
from openclaw_alpha.core.fetcher import DataFetcher
from openclaw_alpha.fetchers.concept_board.models import (
    ConceptBoardFetchParams,
    ConceptBoardFetchResult,
    ConceptBoardItem,
)


class ConceptBoardAkshareFetcher(
    DataFetcher[ConceptBoardFetchParams, ConceptBoardFetchResult]
):
    """概念板块 AKShare 数据获取器

    通过 AKShare 调用东方财富数据源获取概念板块实时行情。

    Attributes:
        name: Fetcher 标识
        data_type: 数据类型
        required_data_source: 需要的数据源（akshare 无需配置）
        priority: 优先级
    """

    name = "akshare_concept"
    data_type = "concept_board"
    required_data_source = "akshare"
    priority = 2

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    def _call_api(self) -> pd.DataFrame:
        """调用 AKShare API 获取概念板块数据

        Returns:
            原始 API 响应 DataFrame

        Raises:
            RateLimitError: 请求限流
            TimeoutError: 请求超时
            ServerError: 服务端错误
            NetworkError: 网络错误
        """
        try:
            df: pd.DataFrame = ak.stock_board_concept_name_em()
            return df
        except Exception as e:
            error_msg = str(e).lower()
            # 根据错误信息转换为对应异常
            if "429" in error_msg or "limit" in error_msg or "freq" in error_msg:
                raise RateLimitError(f"AKShare 请求限流: {e}") from e
            elif "timeout" in error_msg or "timed out" in error_msg:
                raise TimeoutError(f"AKShare 请求超时: {e}") from e
            elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                raise ServerError(f"AKShare 服务端错误: {e}") from e
            elif (
                "connect" in error_msg
                or "network" in error_msg
                or "dns" in error_msg
                or "connection" in error_msg
            ):
                raise NetworkError(f"AKShare 网络错误: {e}") from e
            else:
                # 其他异常不重试，直接抛出
                raise

    def _transform(
        self, df: pd.DataFrame, top: int, sort_by: str
    ) -> list[ConceptBoardItem]:
        """将原始 API 响应转换为业务模型

        Args:
            df: 原始 API 响应 DataFrame
            top: 返回数量限制
            sort_by: 排序字段

        Returns:
            概念板块列表
        """
        if df is None or df.empty:
            return []

        # 确定排序字段
        sort_field_map = {
            "change_pct": "涨跌幅",
            "amount": "总成交额",
            "volume": "总成交量",
            "turnover": "换手率",
        }
        sort_column = sort_field_map.get(sort_by, "涨跌幅")

        # 按排序字段降序排列
        if sort_column in df.columns:
            # 处理可能的字符串类型数据
            df[sort_column] = pd.to_numeric(df[sort_column], errors="coerce")
            df = df.sort_values(by=sort_column, ascending=False)

        # 取前 N 个
        df = df.head(top)

        # 构建结果数据
        items: list[ConceptBoardItem] = []
        for idx, row in enumerate(df.itertuples(), start=1):
            item = self._parse_row(idx, row)
            items.append(item)

        return items

    def _parse_row(self, rank: int, row: Any) -> ConceptBoardItem:
        """解析数据行

        Args:
            rank: 排名
            row: 数据行

        Returns:
            概念板块数据项
        """
        return ConceptBoardItem(
            rank=rank,
            board_code=str(getattr(row, "板块代码", "")),
            board_name=str(getattr(row, "板块名称", "")),
            price=round(float(getattr(row, "最新价", 0) or 0), 2),
            change_pct=round(float(getattr(row, "涨跌幅", 0) or 0), 2),
            change=round(float(getattr(row, "涨跌额", 0) or 0), 2),
            volume=round(float(getattr(row, "总成交量", 0) or 0), 2),
            amount=round(float(getattr(row, "总成交额", 0) or 0), 2),
            turnover_rate=round(float(getattr(row, "换手率", 0) or 0), 2),
            up_count=int(getattr(row, "上涨家数", 0) or 0),
            down_count=int(getattr(row, "下跌家数", 0) or 0),
            leader_name=str(getattr(row, "领涨股票", "")),
            leader_change=round(float(getattr(row, "领涨股票_涨跌幅", 0) or 0), 2),
            total_mv=round(float(getattr(row, "总市值", 0) or 0), 2),
        )

    async def fetch(self, params: ConceptBoardFetchParams) -> ConceptBoardFetchResult:
        """获取概念板块行情数据

        Args:
            params: 获取参数

        Returns:
            概念板块获取结果
        """
        # 调用 API 获取原始数据
        df = self._call_api()

        # 转换数据
        items = self._transform(df, params.top, params.sort_by)

        return ConceptBoardFetchResult(
            trade_date=datetime.now().strftime("%Y-%m-%d"),
            data_source="东方财富",
            items=items,
        )


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        """调试入口"""
        fetcher = ConceptBoardAkshareFetcher()
        result = await fetcher.fetch(ConceptBoardFetchParams(top=10))
        print(f"数据源: {result.data_source}")
        print(f"日期: {result.trade_date}")
        print(f"数量: {len(result.items)}")
        for item in result.items[:5]:
            print(
                f"  {item.rank}. {item.board_name} ({item.board_code}) "
                f"涨跌幅: {item.change_pct}%"
            )

    asyncio.run(main())
