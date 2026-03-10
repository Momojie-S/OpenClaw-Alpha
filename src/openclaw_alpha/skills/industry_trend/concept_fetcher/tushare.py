# -*- coding: utf-8 -*-
"""概念板块数据获取 - Tushare 实现"""

import asyncio
import logging
from typing import Any
from datetime import datetime

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.exceptions import DataSourceUnavailableError

logger = logging.getLogger(__name__)


class ConceptFetcherTushare(FetchMethod):
    """概念板块数据获取 - Tushare 实现

    通过 Tushare 的 concept 接口获取概念板块数据。

    积分要求：2000
    """

    name = "concept_tushare"
    required_data_source = "tushare"
    required_credit = 2000
    priority = 20  # 优先于 AKShare

    async def fetch(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """获取概念板块数据

        Args:
            params: 参数字典，包含：
                - date: 日期（YYYY-MM-DD，用于标识数据日期）
                - src: 来源（默认 'ts'）

        Returns:
            概念板块数据列表，每个元素包含：
                - name: 板块名称
                - code: 板块代码
                - date: 日期
                - metrics: 指标数据
        """
        date = params.get("date", datetime.now().strftime("%Y-%m-%d"))

        # 调用 Tushare API
        data = await self._fetch_concept_data(params.get("src", "ts"))

        # 转换数据格式
        result = self._transform(data, date)

        return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
    )
    async def _fetch_concept_data(self, src: str = "ts") -> pd.DataFrame:
        """获取概念板块数据

        Args:
            src: 来源（ts 或 ths）

        Returns:
            原始概念板块 DataFrame

        Raises:
            DataSourceUnavailableError: API 调用失败
        """
        try:
            client = await self.get_client()
            df = client.concept(src=src)

            if df is None or df.empty:
                logger.warning("无概念板块数据")
                return pd.DataFrame()

            return df

        except Exception as e:
            logger.error(f"获取概念板块数据失败: {e}")
            raise DataSourceUnavailableError(
                data_source_name="tushare",
                reason=f"API 调用失败: {e}"
            ) from e

    def _transform(self, df: pd.DataFrame, date: str) -> list[dict[str, Any]]:
        """转换数据格式

        Args:
            df: 原始数据
            date: 日期

        Returns:
            转换后的数据列表
        """
        if df.empty:
            return []

        result = []

        for _, row in df.iterrows():
            code = str(row.get("code", ""))
            name = str(row.get("name", ""))

            # 跳过无效数据
            if not name or not code:
                continue

            # 构建结果
            result.append({
                "name": name,
                "code": code,
                "date": date,
                "metrics": {
                    # Tushare concept 接口不提供行情数据，只有代码和名称
                    "close": 0.0,
                    "pct_change": 0.0,
                    "amount": 0.0,
                    "turnover_rate": 0.0,
                    "float_mv": 0.0,
                    "up_count": 0,
                    "down_count": 0,
                }
            })

        return result


if __name__ == "__main__":
    # 调试入口
    async def main():
        params = {
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        fetcher = ConceptFetcherTushare()
        result = await fetcher.fetch(params)
        print(f"获取到 {len(result)} 条数据")
        if result:
            print("第一条数据：")
            print(result[0])

    asyncio.run(main())
