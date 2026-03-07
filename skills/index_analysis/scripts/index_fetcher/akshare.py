# -*- coding: utf-8 -*-
"""指数行情获取器 - AKShare 实现"""

import logging
from datetime import datetime
from typing import Any, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.exceptions import NetworkError, RateLimitError, ServerError, TimeoutError
from openclaw_alpha.core.fetcher import FetchMethod

logger = logging.getLogger(__name__)


class IndexFetcherAkshare(FetchMethod):
    """指数行情获取器 - AKShare 实现"""

    name = "index_akshare"
    required_data_source = "akshare"
    priority = 10

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    async def _call_api(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Any:
        """
        调用 AKShare API 获取指数数据。

        Args:
            symbol: 指数代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            原始 DataFrame

        Raises:
            NetworkError: 网络错误
            RateLimitError: 限流
            ServerError: 服务端错误
            TimeoutError: 超时
        """
        import akshare as ak

        try:
            df = ak.stock_zh_index_daily_em(
                symbol=symbol,
                start_date=start_date or "19900101",
                end_date=end_date or "20500101",
            )
            return df
        except Exception as e:
            error_str = str(e).lower()
            if "timeout" in error_str or "timed out" in error_str:
                raise TimeoutError(f"AKShare 请求超时: {e}")
            elif "rate limit" in error_str or "too many" in error_str:
                raise RateLimitError(f"AKShare 限流: {e}")
            elif "server error" in error_str or "500" in error_str or "502" in error_str or "503" in error_str:
                raise ServerError(f"AKShare 服务端错误: {e}")
            elif "connection" in error_str or "network" in error_str:
                raise NetworkError(f"AKShare 网络错误: {e}")
            else:
                raise

    def _transform(self, raw_data: Any) -> list[dict]:
        """
        转换原始数据为标准格式。

        Args:
            raw_data: AKShare DataFrame

        Returns:
            标准格式的行情数据列表
        """
        if raw_data is None or raw_data.empty:
            return []

        result = []
        for _, row in raw_data.iterrows():
            # 处理日期格式
            date_val = row.get("date")
            if hasattr(date_val, "strftime"):
                date_str = date_val.strftime("%Y-%m-%d")
            else:
                date_str = str(date_val)

            item = {
                "date": date_str,
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "volume": int(row.get("volume", 0)),
                "amount": float(row.get("amount", 0)),
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

        raw_data = await self._call_api(symbol, start_date, end_date)
        return self._transform(raw_data)


# 调试入口
if __name__ == "__main__":
    import asyncio
    import json

    async def main():
        fetcher = IndexFetcherAkshare()
        # 获取上证指数最近数据
        data = await fetcher.fetch({"symbol": "sh000001"})
        print(f"获取到 {len(data)} 条数据")
        if data:
            print("最近5条:")
            print(json.dumps(data[-5:], ensure_ascii=False, indent=2))

    asyncio.run(main())
