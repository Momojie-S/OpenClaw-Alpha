# -*- coding: utf-8 -*-
"""申万行业数据获取 - Tushare 实现"""

import asyncio
from typing import Any
from datetime import datetime

from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.registry import DataSourceRegistry


class IndustryFetcherTushare(FetchMethod):
    """申万行业数据获取 - Tushare 实现
    
    通过 Tushare 获取申万行业分类和日线行情数据。
    """
    
    name = "industry_tushare"
    required_data_source = "tushare"
    priority = 10
    
    async def fetch(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """获取申万行业数据
        
        Args:
            params: 参数字典，包含：
                - category: 行业层级（L1/L2/L3）
                - date: 日期（YYYY-MM-DD）
        
        Returns:
            行业数据列表，每个元素包含：
                - name: 行业名称
                - code: 行业代码
                - level: 行业层级
                - date: 日期
                - metrics: 指标数据（涨跌幅、换手率、成交额、流通市值等）
        """
        category = params.get("category", "L1")
        date = params.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        # 1. 获取行业分类
        classifications = await self._fetch_classifications(category)
        
        # 2. 获取日线行情
        daily_data = await self._fetch_daily_data(date)
        
        # 3. 合并数据
        result = self._merge_data(classifications, daily_data, category, date)
        
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
        """获取日线行情
        
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
        
        # 调用 Tushare API
        df = client.sw_daily(trade_date=trade_date)
        
        # 转换为字典列表
        daily_data = df.to_dict('records')
        
        return daily_data
    
    def _merge_data(
        self,
        classifications: list[dict],
        daily_data: list[dict],
        category: str,
        date: str,
    ) -> list[dict[str, Any]]:
        """合并分类数据和行情数据
        
        Args:
            classifications: 行业分类数据
            daily_data: 日线行情数据
            category: 行业层级
            date: 日期
        
        Returns:
            合并后的行业数据列表
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
            
            # 构建结果
            result.append({
                'name': cls['industry_name'],
                'code': code,
                'level': category,
                'date': date,
                'metrics': {
                    'close': float(daily['close']),
                    'pct_change': float(daily['pct_change']),
                    'amount': float(daily['amount']),  # 万元
                    'turnover_rate': self._calc_turnover_rate(daily),
                    'float_mv': float(daily['float_mv']),  # 万元
                }
            })
        
        return result
    
    def _calc_turnover_rate(self, daily: dict) -> float:
        """计算换手率
        
        换手率 = 成交额 / 流通市值 × 100%
        
        Args:
            daily: 日线数据
        
        Returns:
            换手率（%）
        """
        amount = float(daily['amount'])
        float_mv = float(daily['float_mv'])
        
        if float_mv == 0:
            return 0.0
        
        return (amount / float_mv) * 100


if __name__ == "__main__":
    # 导入数据源以触发注册
    from openclaw_alpha.data_sources import registry  # noqa: F401
    
    # 调试入口
    async def main():
        params = {
            "category": "L1",
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        fetcher = IndustryFetcherTushare()
        result = await fetcher.fetch(params)
        print(f"获取到 {len(result)} 条数据")
        if result:
            print("第一条数据：")
            print(result[0])
    
    asyncio.run(main())
