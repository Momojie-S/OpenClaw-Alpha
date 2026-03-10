# -*- coding: utf-8 -*-
"""概念板块数据获取 - AKShare 实现"""

import asyncio
from typing import Any
from datetime import datetime

from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.core.registry import DataSourceRegistry


class ConceptFetcherAkshare(FetchMethod):
    """概念板块数据获取 - AKShare 实现
    
    通过 AKShare 获取东方财富概念板块数据。
    """
    
    name = "concept_akshare"
    required_data_source = "akshare"
    priority = 10
    
    async def fetch(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """获取概念板块数据
        
        Args:
            params: 参数字典，包含：
                - date: 日期（YYYY-MM-DD，用于标识数据日期）
        
        Returns:
            概念板块数据列表，每个元素包含：
                - name: 板块名称
                - code: 板块代码
                - date: 日期
                - metrics: 指标数据（涨跌幅、换手率、成交额、涨跌家数等）
        """
        date = params.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        # 调用 AKShare API
        data = await self._fetch_concept_data()
        
        # 转换数据格式
        result = self._transform(data, date)
        
        return result
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
    )
    async def _fetch_concept_data(self) -> list[dict]:
        """获取概念板块数据
        
        Returns:
            原始概念板块数据列表
        """
        registry = DataSourceRegistry.get_instance()
        akshare = registry.get("akshare")
        client = await akshare.get_client()
        
        # 调用 AKShare API
        df = client.stock_board_concept_name_em()
        
        # 转换为字典列表
        data = df.to_dict('records')
        
        return data
    
    def _transform(self, data: list[dict], date: str) -> list[dict[str, Any]]:
        """转换数据格式
        
        Args:
            data: 原始数据
            date: 日期
        
        Returns:
            转换后的数据列表
        
        Note:
            AKShare 的 stock_board_concept_name_em 接口不返回成交额，
            使用 总市值 × 换手率 / 100 估算成交额（换手率基于流通市值，此处用总市值近似）
        """
        result = []
        
        for item in data:
            # 提取字段
            name = item.get('板块名称', '')
            code = item.get('板块代码', '')
            
            # 跳过无效数据
            if not name or not code:
                continue
            
            # 估算成交额：总市值 × 换手率 / 100
            total_mv = self._parse_float(item.get('总市值'), 0.0)
            turnover_rate = self._parse_float(item.get('换手率'), 0.0)
            estimated_amount = total_mv * turnover_rate / 100 if total_mv > 0 and turnover_rate > 0 else 0.0
            
            # 构建结果
            result.append({
                'name': name,
                'code': code,
                'date': date,
                'metrics': {
                    'close': self._parse_float(item.get('最新价')),
                    'pct_change': self._parse_float(item.get('涨跌幅')),
                    'amount': estimated_amount / 10000,  # 元 -> 万元
                    'turnover_rate': turnover_rate,
                    'float_mv': total_mv / 10000,  # 元 -> 万元（使用总市值代替流通市值）
                    'up_count': self._parse_int(item.get('上涨家数')),
                    'down_count': self._parse_int(item.get('下跌家数')),
                }
            })
        
        return result
    
    def _parse_float(self, value: Any, default: float = 0.0) -> float:
        """解析浮点数
        
        Args:
            value: 原始值
            default: 默认值
        
        Returns:
            浮点数
        """
        if value is None:
            return default
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _parse_int(self, value: Any, default: int = 0) -> int:
        """解析整数
        
        Args:
            value: 原始值
            default: 默认值
        
        Returns:
            整数
        """
        if value is None:
            return default
        
        try:
            return int(value)
        except (ValueError, TypeError):
            return default


if __name__ == "__main__":
    # 调试入口
    async def main():
        params = {
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        fetcher = ConceptFetcherAkshare()
        result = await fetcher.fetch(params)
        print(f"获取到 {len(result)} 条数据")
        if result:
            print("第一条数据：")
            print(result[0])
    
    asyncio.run(main())
