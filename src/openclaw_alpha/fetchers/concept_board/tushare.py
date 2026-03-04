# -*- coding: utf-8 -*-
"""概念板块 Tushare 数据获取器"""

from datetime import datetime

import pandas as pd

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

    async def fetch(self, params: ConceptBoardFetchParams) -> ConceptBoardFetchResult:
        """获取概念板块行情数据

        Args:
            params: 获取参数

        Returns:
            概念板块获取结果
        """
        import tushare as ts
        import os

        api_token = os.environ.get("TUSHARE_TOKEN")
        if not api_token:
            raise ValueError("TUSHARE_TOKEN 未配置")

        pro = ts.pro_api(api_token)

        # 获取概念板块分类
        # 注意：Tushare 概念板块数据接口可能需要积分
        # 使用 concept 接口获取概念分类
        df: pd.DataFrame = pro.concept()

        if df is None or df.empty:
            return ConceptBoardFetchResult(
                trade_date=datetime.now().strftime("%Y-%m-%d"),
                data_source="Tushare",
                items=[],
            )

        # 由于 Tushare 概念板块接口不直接提供行情数据，
        # 这里只返回分类信息，实际使用时建议使用 AKShare Fetcher
        items: list[ConceptBoardItem] = []
        for idx, row in enumerate(df.head(params.top).itertuples(), start=1):
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

        return ConceptBoardFetchResult(
            trade_date=datetime.now().strftime("%Y-%m-%d"),
            data_source="Tushare",
            items=items,
        )
