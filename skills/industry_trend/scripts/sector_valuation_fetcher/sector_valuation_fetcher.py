# -*- coding: utf-8 -*-
"""行业估值 Fetcher 入口"""

from openclaw_alpha.core.fetcher import Fetcher
from .tushare import SectorValuationFetcherTushare


class SectorValuationFetcher(Fetcher):
    """行业估值数据获取器

    支持：
    - Tushare（优先）：申万行业日线行情（包含 PE/PB）
    """

    name = "sector_valuation"

    def __init__(self):
        """初始化并注册实现"""
        super().__init__()
        # 注册 Tushare 实现，优先级 10
        self.register(SectorValuationFetcherTushare(), priority=10)


async def fetch(category: str = "L1", date: str = None) -> list[dict]:
    """获取行业估值数据

    Args:
        category: 行业层级（L1/L2/L3/concept）
        date: 日期（YYYY-MM-DD），默认当日

    Returns:
        行业估值数据列表
    """
    from datetime import datetime
    # 导入数据源以触发注册
    from openclaw_alpha.data_sources import registry  # noqa: F401

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    fetcher = SectorValuationFetcher()
    params = {"category": category, "date": date}
    return await fetcher.fetch(params)


if __name__ == "__main__":
    # 导入数据源以触发注册
    from openclaw_alpha.data_sources import registry  # noqa: F401
    import asyncio
    import json

    async def main():
        result = await fetch(category="L1")
        print(f"获取到 {len(result)} 条数据")
        if result:
            print("第一条数据：")
            print(json.dumps(result[0], ensure_ascii=False, indent=2))

    asyncio.run(main())
