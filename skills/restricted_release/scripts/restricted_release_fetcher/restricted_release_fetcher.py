# -*- coding: utf-8 -*-
"""限售解禁数据 Fetcher"""

import asyncio
from typing import Any

import akshare as ak
import pandas as pd

from openclaw_alpha.core.fetcher import Fetcher, FetchMethod


class RestrictedReleaseFetcherAkshare(FetchMethod):
    """AKShare 限售解禁数据获取"""

    name = "restricted_release_akshare"
    required_data_source = "akshare"
    priority = 10

    async def _fetch_upcoming(
        self, start_date: str, end_date: str
    ) -> list[dict[str, Any]]:
        """
        获取即将解禁的股票详情

        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            解禁股票列表
        """
        # AKShare 接口是同步的，使用 run_in_executor
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None,
            lambda: ak.stock_restricted_release_detail_em(
                start_date=start_date, end_date=end_date
            ),
        )

        if df.empty:
            return []

        # 转换为 dict 列表
        return self._transform_detail(df)

    async def _fetch_queue(self, symbol: str) -> list[dict[str, Any]]:
        """
        获取单只股票的解禁排期

        Args:
            symbol: 股票代码

        Returns:
            解禁排期列表
        """
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None, lambda: ak.stock_restricted_release_queue_em(symbol=symbol)
        )

        if df.empty:
            return []

        return self._transform_queue(df)

    async def _fetch_summary(
        self, start_date: str, end_date: str
    ) -> list[dict[str, Any]]:
        """
        获取按日期汇总的解禁情况

        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            每日解禁汇总列表
        """
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None,
            lambda: ak.stock_restricted_release_summary_em(
                symbol="全部股票", start_date=start_date, end_date=end_date
            ),
        )

        if df.empty:
            return []

        return self._transform_summary(df)

    def _transform_detail(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """转换解禁详情数据"""
        records = df.to_dict("records")
        result = []

        for record in records:
            result.append(
                {
                    "code": str(record.get("股票代码", "")),
                    "name": str(record.get("股票简称", "")),
                    "release_date": str(record.get("解禁时间", "")),
                    "restricted_type": str(record.get("限售股类型", "")),
                    "release_volume": float(record.get("解禁数量", 0) or 0),
                    "actual_release_volume": float(record.get("实际解禁数量", 0) or 0),
                    "actual_release_value": float(record.get("实际解禁市值", 0) or 0),
                    "ratio_to_circulation": float(
                        record.get("占解禁前流通市值比例", 0) or 0
                    ),
                    "pre_close_price": float(record.get("解禁前一交易日收盘价", 0) or 0),
                }
            )

        return result

    def _transform_queue(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """转换单只股票解禁排期数据"""
        records = df.to_dict("records")
        result = []

        for record in records:
            result.append(
                {
                    "release_date": str(record.get("解禁时间", "")),
                    "shareholder_count": int(record.get("解禁股东数", 0) or 0),
                    "release_volume": float(record.get("解禁数量", 0) or 0),
                    "actual_release_volume": float(record.get("实际解禁数量", 0) or 0),
                    "unreleased_volume": float(record.get("未解禁数量", 0) or 0),
                    "actual_release_value": float(record.get("实际解禁数量市值", 0) or 0),
                    "ratio_to_total": float(record.get("占总市值比例", 0) or 0),
                    "ratio_to_circulation": float(record.get("占流通市值比例", 0) or 0),
                    "pre_close_price": float(record.get("解禁前一交易日收盘价", 0) or 0),
                    "restricted_type": str(record.get("限售股类型", "")),
                }
            )

        return result

    def _transform_summary(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """转换汇总数据"""
        records = df.to_dict("records")
        result = []

        for record in records:
            result.append(
                {
                    "release_date": str(record.get("解禁时间", "")),
                    "stock_count": int(record.get("当日解禁股票家数", 0) or 0),
                    "release_volume": float(record.get("解禁数量", 0) or 0),
                    "actual_release_volume": float(record.get("实际解禁数量", 0) or 0),
                    "actual_release_value": float(record.get("实际解禁市值", 0) or 0),
                }
            )

        return result

    async def fetch(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        统一获取接口

        Args:
            params: 参数字典
                - mode: "upcoming" | "queue" | "summary"
                - start_date: 开始日期 (YYYYMMDD)
                - end_date: 结束日期 (YYYYMMDD)
                - symbol: 股票代码 (mode=queue 时必填)

        Returns:
            数据字典，包含 data 和 meta 信息
        """
        mode = params.get("mode", "upcoming")
        start_date = params.get("start_date", "")
        end_date = params.get("end_date", "")

        if mode == "upcoming":
            data = await self._fetch_upcoming(start_date, end_date)
            return {
                "mode": "upcoming",
                "data": data,
                "meta": {"start_date": start_date, "end_date": end_date},
            }

        elif mode == "queue":
            symbol = params.get("symbol", "")
            if not symbol:
                return {"mode": "queue", "data": [], "meta": {"error": "缺少股票代码"}}

            data = await self._fetch_queue(symbol)
            return {"mode": "queue", "data": data, "meta": {"symbol": symbol}}

        elif mode == "summary":
            data = await self._fetch_summary(start_date, end_date)
            return {
                "mode": "summary",
                "data": data,
                "meta": {"start_date": start_date, "end_date": end_date},
            }

        else:
            return {"mode": mode, "data": [], "meta": {"error": f"未知模式: {mode}"}}


class RestrictedReleaseFetcher(Fetcher):
    """限售解禁数据 Fetcher 入口"""

    name = "restricted_release"

    def __init__(self):
        super().__init__()
        # 注册 AKShare 实现
        self.register(RestrictedReleaseFetcherAkshare())
