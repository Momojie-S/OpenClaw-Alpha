# -*- coding: utf-8 -*-
"""行业估值数据获取 - Tushare 实现"""

import asyncio
from typing import Any
from datetime import datetime

from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.registry import DataSourceRegistry


class SectorValuationFetcherTushare(FetchMethod):
    """行业估值数据获取 - Tushare 实现

    通过 Tushare sw_daily 获取申万行业估值数据（PE/PB）。
    """

    name = "sector_valuation_tushare"
    required_data_source = "tushare"
    required_credit = 5000
    priority = 10

    async def fetch(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """获取行业估值数据

        Args:
            params: 参数字典，包含：
                - category: 行业层级（L1/L2/L3）
                - date: 日期（YYYY-MM-DD）

        Returns:
            行业估值数据列表，每个元素包含：
                - name: 行业名称
                - code: 行业代码
                - level: 行业层级
                - date: 日期
                - pe: 市盈率
                - pb: 市净率
                - pct_change: 涨跌幅
                - float_mv: 流通市值（万元）
                - total_mv: 总市值（万元）
        """
        category = params.get("category", "L1")
        date = params.get("date", datetime.now().strftime("%Y-%m-%d"))

        # 1. 获取行业分类
        classifications = await self._fetch_classifications(category)

        # 2. 获取日线行情（包含 PE/PB）
        daily_data = await self._fetch_daily_data(date)

        # 3. 提取估值数据
        result = self._extract_valuation(classifications, daily_data, category, date)

        return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
    )
    async def _fetch_classifications(self, category: str) -> list[dict]:
        """获取行业分类

        Args:
            category: 行业层级（L1/L2/L3）

        Returns:
            行业分类列表
        """
        registry = DataSourceRegistry.get_instance()
        tushare = registry.get("tushare")
        client = await tushare.get_client()

        # 调用 Tushare API
        df = client.index_classify(level=category, src='SW2021')

        # 转换为字典列表
        classifications = df.to_dict('records')

        return classifications

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
    )
    async def _fetch_daily_data(self, date: str) -> list[dict]:
        """获取日线行情（包含 PE/PB）

        Args:
            date: 日期（YYYY-MM-DD）

        Returns:
            日线行情列表
        """
        registry = DataSourceRegistry.get_instance()
        tushare = registry.get("tushare")
        client = await tushare.get_client()

        # 转换日期格式：YYYY-MM-DD -> YYYYMMDD
        trade_date = date.replace("-", "")

        # 调用 Tushare API - sw_daily 包含 PE/PB
        df = client.sw_daily(trade_date=trade_date)

        # 转换为字典列表
        daily_data = df.to_dict('records')

        return daily_data

    def _extract_valuation(
        self,
        classifications: list[dict],
        daily_data: list[dict],
        category: str,
        date: str,
    ) -> list[dict[str, Any]]:
        """提取估值数据

        Args:
            classifications: 行业分类数据
            daily_data: 日线行情数据
            category: 行业层级
            date: 日期

        Returns:
            估值数据列表
        """
        # 构建 code -> daily_data 的映射
        daily_map = {item['ts_code']: item for item in daily_data}

        result = []
        for cls in classifications:
            code = cls['index_code']

            # 获取对应的行情数据
            daily = daily_map.get(code)
            if not daily:
                continue

            # 提取估值数据
            pe = daily.get('pe')
            pb = daily.get('pb')

            # 跳过无估值数据的板块
            if pe is None or pb is None:
                continue

            result.append({
                'name': cls['industry_name'],
                'code': code,
                'level': category,
                'date': date,
                'pe': float(pe) if pe else None,
                'pb': float(pb) if pb else None,
                'pct_change': float(daily['pct_change']),
                'float_mv': float(daily['float_mv']),  # 万元
                'total_mv': float(daily['total_mv']),  # 万元
            })

        return result


if __name__ == "__main__":
    # 导入数据源以触发注册
    from openclaw_alpha.data_sources import registry  # noqa: F401

    # 调试入口
    async def main():
        # 使用最近的交易日（周五）
        params = {
            "category": "L1",
            "date": "2026-03-06",  # 周五
        }
        fetcher = SectorValuationFetcherTushare()
        result = await fetcher.fetch(params)
        print(f"获取到 {len(result)} 条数据")
        if result:
            print("前3条数据：")
            import json
            for item in result[:3]:
                print(json.dumps(item, ensure_ascii=False, indent=2))
        else:
            # 调试：打印分类和日线数据
            print("调试：获取分类...")
            classifications = await fetcher._fetch_classifications("L1")
            print(f"分类数量: {len(classifications)}")
            if classifications:
                print(f"示例分类: {classifications[0]}")

            print("\n调试：获取日线数据...")
            daily_data = await fetcher._fetch_daily_data("2026-03-06")
            print(f"日线数据数量: {len(daily_data)}")
            if daily_data:
                print(f"示例日线: {daily_data[0]}")

    asyncio.run(main())
