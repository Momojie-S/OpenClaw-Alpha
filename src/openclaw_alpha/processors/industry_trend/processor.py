# -*- coding: utf-8 -*-
"""产业趋势分析加工器"""

from datetime import datetime

from openclaw_alpha.core.processor import DataProcessor
from openclaw_alpha.fetchers.concept_board import (
    ConceptBoardAkshareFetcher,
    ConceptBoardFetchParams,
)
from openclaw_alpha.fetchers.sw_industry import (
    SwIndustryFetchParams,
    SwIndustryTushareFetcher,
)
from openclaw_alpha.processors.industry_trend.models import (
    BoardTrendItem,
    IndustryTrendProcessParams,
    IndustryTrendProcessResult,
)


class IndustryTrendProcessor(
    DataProcessor[IndustryTrendProcessParams, IndustryTrendProcessResult]
):
    """产业趋势分析加工器

    组合概念板块和申万行业数据，提供产业趋势分析。

    Attributes:
        name: Processor 标识
        required_data_types: 需要的数据类型列表
    """

    name = "industry_trend"
    required_data_types = ["concept_board", "sw_industry"]

    async def process(self, params: IndustryTrendProcessParams) -> IndustryTrendProcessResult:
        """执行产业趋势分析

        Args:
            params: 加工参数

        Returns:
            产业趋势分析结果
        """
        # 获取概念板块数据
        concept_items = await self._fetch_concept_boards(params)

        # 获取申万行业数据
        sw_industry_items = await self._fetch_sw_industries(params)

        # 获取交易日期
        trade_date = datetime.now().strftime("%Y-%m-%d")
        if sw_industry_items:
            # 从申万行业数据获取交易日期
            trade_date = self._format_trade_date(
                sw_industry_items[0].data_source.split(":")[-1]
                if ":" in sw_industry_items[0].data_source
                else trade_date
            )

        return IndustryTrendProcessResult(
            trade_date=trade_date,
            concept_boards=concept_items,
            sw_industries=sw_industry_items,
        )

    async def _fetch_concept_boards(
        self, params: IndustryTrendProcessParams
    ) -> list[BoardTrendItem]:
        """获取概念板块数据

        Args:
            params: 加工参数

        Returns:
            概念板块趋势数据列表
        """
        try:
            fetcher = self.get_available_fetcher("concept_board")
            fetch_params = ConceptBoardFetchParams(
                top=params.top,
                sort_by=params.sort_by,
            )
            result = await fetcher.fetch(fetch_params)

            items: list[BoardTrendItem] = []
            for item in result.items:
                trend_item = BoardTrendItem(
                    rank=item.rank,
                    board_code=item.board_code,
                    board_name=item.board_name,
                    change_pct=item.change_pct,
                    turnover_rate=item.turnover_rate,
                    amount=item.amount / 100000000,  # 转换为亿元
                    data_source=f"concept_board:{result.data_source}",
                )
                items.append(trend_item)

            return items
        except Exception:
            # 如果获取失败，返回空列表
            return []

    async def _fetch_sw_industries(
        self, params: IndustryTrendProcessParams
    ) -> list[BoardTrendItem]:
        """获取申万行业数据

        Args:
            params: 加工参数

        Returns:
            申万行业趋势数据列表
        """
        try:
            fetcher = self.get_available_fetcher("sw_industry")
            fetch_params = SwIndustryFetchParams(
                top=params.top,
                sort_by=params.sort_by,
            )
            result = await fetcher.fetch(fetch_params)

            items: list[BoardTrendItem] = []
            for item in result.items:
                trend_item = BoardTrendItem(
                    rank=item.rank,
                    board_code=item.board_code,
                    board_name=item.board_name,
                    change_pct=item.change_pct,
                    turnover_rate=item.turnover_rate,
                    amount=item.amount,  # 已经是亿元
                    data_source=f"sw_industry:{result.data_source}",
                )
                items.append(trend_item)

            return items
        except Exception:
            # 如果获取失败，返回空列表
            return []

    def _format_trade_date(self, trade_date: str) -> str:
        """格式化交易日期

        Args:
            trade_date: 交易日期（YYYYMMDD 或 YYYY-MM-DD）

        Returns:
            格式化后的日期（YYYY-MM-DD）
        """
        if len(trade_date) == 8:
            return f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
        return trade_date
