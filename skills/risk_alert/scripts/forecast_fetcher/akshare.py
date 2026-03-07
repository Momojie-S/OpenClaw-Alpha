# -*- coding: utf-8 -*-
"""业绩预告 Fetcher - AKShare 实现"""

import asyncio
from typing import Any

import akshare as ak

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.data_sources import registry


class ForecastFetcherAkshare(FetchMethod):
    """业绩预告数据获取器 - AKShare 实现"""

    name = "forecast_akshare"
    required_data_source = "akshare"
    priority = 10

    # 风险等级映射
    RISK_LEVELS = {
        "首亏": "高",
        "预减": "高",
        "增亏": "高",
        "续亏": "高",
        "不确定": "中",
        "略减": "中",
        "预增": "无",
        "略增": "无",
        "扭亏": "无",
        "减亏": "无",
        "续盈": "无",
    }

    # 高风险类型
    HIGH_RISK_TYPES = {"首亏", "预减", "增亏", "续亏"}

    # 中风险类型
    MEDIUM_RISK_TYPES = {"不确定", "略减"}

    async def fetch(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """
        获取业绩预告数据

        Args:
            params: 参数字典
                - date: 日期，格式 YYYY-MM-DD（可选）

        Returns:
            业绩预告列表
        """
        # AKShare 不支持按日期筛选，获取所有数据后过滤
        df = await self._call_api()

        # 转换数据
        records = self._transform(df)

        # 按日期过滤
        if params.get("date"):
            records = [r for r in records if r["announce_date"] == params["date"]]

        # 按风险类型过滤
        if params.get("risk_type"):
            if params["risk_type"] == "高":
                records = [r for r in records if r["forecast_type"] in self.HIGH_RISK_TYPES]
            elif params["risk_type"] == "中":
                records = [r for r in records if r["forecast_type"] in self.MEDIUM_RISK_TYPES]

        return records

    async def _call_api(self) -> Any:
        """调用 AKShare API"""
        # AKShare 的这个接口是同步的，需要在 executor 中运行
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(None, ak.stock_yjyg_em)
        return df

    def _transform(self, df: Any) -> list[dict[str, Any]]:
        """
        转换数据格式

        Args:
            df: AKShare 返回的 DataFrame

        Returns:
            转换后的列表
        """
        records = []

        for _, row in df.iterrows():
            record = {
                "code": row["股票代码"],
                "name": row["股票简称"],
                "indicator": row["预测指标"],
                "change_desc": row["业绩变动"],
                "forecast_value": row["预测数值"],
                "change_pct": row["业绩变动幅度"],
                "change_reason": row["业绩变动原因"],
                "forecast_type": row["预告类型"],
                "last_year_value": row["上年同期值"],
                "announce_date": row["公告日期"],
                "risk_level": self.RISK_LEVELS.get(row["预告类型"], "未知"),
            }
            records.append(record)

        return records

    def is_available(self) -> tuple[bool, str | None]:
        """检查是否可用"""
        # AKShare 无需配置
        return True, None


def __main__():
    """调试入口"""
    import json

    async def test():
        fetcher = ForecastFetcherAkshare()
        records = await fetcher.fetch({})
        print(f"获取到 {len(records)} 条业绩预告")
        print("\n前 5 条（高风险）:")
        high_risk = [r for r in records if r["risk_level"] == "高"]
        print(json.dumps(high_risk[:5], ensure_ascii=False, indent=2, default=str))

    asyncio.run(test())


if __name__ == "__main__":
    __main__()
