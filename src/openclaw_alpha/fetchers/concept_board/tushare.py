# -*- coding: utf-8 -*-
"""概念板块 Tushare 数据获取器"""

import os
from datetime import datetime

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
from openclaw_alpha.fetchers.concept_board.models import (
    ConceptBoardFetchParams,
    ConceptBoardFetchResult,
    ConceptBoardItem,
)


class ConceptBoardTushareFetcher(
    DataFetcher[ConceptBoardFetchParams, ConceptBoardFetchResult]
):
    """概念板块 Tushare 数据获取器

    通过 Tushare Pro API 获取概念板块行情数据。
    注意：Tushare 概念板块数据可能需要较高积分。

    Attributes:
        name: Fetcher 标识
        data_type: 数据类型
        required_data_source: 需要的数据源
        priority: 优先级（低于 AKShare）
    """

    name = "tushare_concept"
    data_type = "concept_board"
    required_data_source = "tushare"
    priority = 1

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    def _call_api(self) -> pd.DataFrame:
        """调用 Tushare API 获取概念板块分类

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
            df: pd.DataFrame = pro.concept()
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

    def _transform(self, df: pd.DataFrame, top: int) -> list[ConceptBoardItem]:
        """将原始 API 响应转换为业务模型

        Args:
            df: 原始 API 响应 DataFrame
            top: 返回数量限制

        Returns:
            概念板块列表
        """
        if df is None or df.empty:
            return []

        items: list[ConceptBoardItem] = []
        for idx, row in enumerate(df.head(top).itertuples(), start=1):
            item = ConceptBoardItem(
                rank=idx,
                board_code=str(getattr(row, "code", "")),
                board_name=str(getattr(row, "name", "")),
                price=0.0,
                change_pct=0.0,
                change=0.0,
                volume=0.0,
                amount=0.0,
                turnover_rate=0.0,
                up_count=0,
                down_count=0,
                leader_name="",
                leader_change=0.0,
                total_mv=0.0,
            )
            items.append(item)

        return items

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
        items = self._transform(df, params.top)

        return ConceptBoardFetchResult(
            trade_date=datetime.now().strftime("%Y-%m-%d"),
            data_source="Tushare",
            items=items,
        )


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        """调试入口"""
        fetcher = ConceptBoardTushareFetcher()
        result = await fetcher.fetch(ConceptBoardFetchParams(top=10))
        print(f"数据源: {result.data_source}")
        print(f"日期: {result.trade_date}")
        print(f"数量: {len(result.items)}")
        for item in result.items[:5]:
            print(f"  {item.rank}. {item.board_name} ({item.board_code})")

    asyncio.run(main())
