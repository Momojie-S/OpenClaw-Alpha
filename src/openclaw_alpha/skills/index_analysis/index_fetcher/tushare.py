# -*- coding: utf-8 -*-
"""指数行情获取器 - Tushare 实现"""

import logging
from typing import Any, Optional

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.exceptions import DataSourceUnavailableError

logger = logging.getLogger(__name__)


# 指数代码映射（AKShare 格式 -> Tushare 格式）
SYMBOL_MAP = {
    "sh000001": "000001.SH",  # 上证指数
    "sz399001": "399001.SZ",  # 深证成指
    "sh000016": "000016.SH",  # 上证50
    "sh000300": "000300.SH",  # 沪深300
    "sz399005": "399005.SZ",  # 中小板指
    "sz399006": "399006.SZ",  # 创业板指
    "sh000905": "000905.SH",  # 中证500
    "sh000688": "000688.SH",  # 科创50
}


class IndexFetcherTushare(FetchMethod):
    """指数行情获取器 - Tushare 实现

    使用 Tushare 的 index_daily 接口获取指数日线数据。

    积分要求：2000
    """

    name = "index_tushare"
    required_data_source = "tushare"
    required_credit = 2000
    priority = 20  # 优先于 AKShare

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    async def _call_api(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        调用 Tushare API 获取指数数据。

        Args:
            ts_code: Tushare 指数代码
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）

        Returns:
            原始 DataFrame

        Raises:
            DataSourceUnavailableError: API 调用失败
        """
        try:
            client = await self.get_client()

            # 构造参数
            params = {"ts_code": ts_code}
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date

            df = client.index_daily(**params)

            if df is None or df.empty:
                logger.warning(f"指数 {ts_code} 无数据")
                return pd.DataFrame()

            return df

        except Exception as e:
            logger.error(f"获取指数数据失败: {e}")
            raise DataSourceUnavailableError(
                data_source_name="tushare",
                reason=f"API 调用失败: {e}"
            ) from e

    def _transform(self, raw_data: pd.DataFrame) -> list[dict]:
        """
        转换原始数据为标准格式。

        Args:
            raw_data: Tushare DataFrame

        Returns:
            标准格式的行情数据列表
        """
        if raw_data is None or raw_data.empty:
            return []

        result = []
        for _, row in raw_data.iterrows():
            # 处理日期格式
            trade_date = str(row.get("trade_date", ""))
            if trade_date:
                date_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
            else:
                date_str = ""

            item = {
                "date": date_str,
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "volume": int(row.get("vol", 0) * 100),  # 万手 -> 手
                "amount": float(row.get("amount", 0) * 10000),  # 千元 -> 元
            }
            result.append(item)

        # 按日期排序（旧到新）
        result.sort(key=lambda x: x["date"])
        return result

    async def fetch(self, params: dict) -> list[dict]:
        """
        获取指数历史行情数据。

        Args:
            params: 参数字典，包含 symbol, start_date, end_date

        Returns:
            行情数据列表
        """
        symbol = params.get("symbol")
        start_date = params.get("start_date")
        end_date = params.get("end_date")

        # 转换代码格式
        ts_code = SYMBOL_MAP.get(symbol)
        if not ts_code:
            # 尝试直接使用（用户可能传入了 Tushare 格式）
            ts_code = symbol

        raw_data = await self._call_api(ts_code, start_date, end_date)
        return self._transform(raw_data)


# 调试入口
if __name__ == "__main__":
    import asyncio
    import json

    async def main():
        fetcher = IndexFetcherTushare()
        # 获取上证指数最近数据
        data = await fetcher.fetch({"symbol": "sh000001"})
        print(f"获取到 {len(data)} 条数据")
        if data:
            print("最近5条:")
            print(json.dumps(data[-5:], ensure_ascii=False, indent=2))

    asyncio.run(main())
