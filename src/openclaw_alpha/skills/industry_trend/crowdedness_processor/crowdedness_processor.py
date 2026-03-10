# -*- coding: utf-8 -*-
"""板块拥挤度指标 Processor"""

import argparse
import asyncio
import json
from datetime import datetime
from typing import Any

from openclaw_alpha.core.processor_utils import get_output_path
# 导入数据源模块以触发注册
from openclaw_alpha.data_sources import registry  # noqa: F401

from openclaw_alpha.skills.industry_trend.industry_fetcher import fetch as fetch_industry
from openclaw_alpha.skills.industry_trend.concept_fetcher import fetch as fetch_concept


# 常量定义
SKILL_NAME = "industry-trend"
PROCESSOR_NAME = "crowdedness"

# 拥挤度权重
CROWDEDNESS_WEIGHTS = {
    "turnover_rate_percentile": 0.50,  # 换手率分位
    "volume_ratio_percentile": 0.50,   # 成交额占比分位
}

# 拥挤度等级阈值
CROWDEDNESS_LEVELS = {
    "high": (80, "高拥挤"),
    "medium": (50, "中等拥挤"),
    "low": (0, "低拥挤"),
}


class CrowdednessProcessor:
    """板块拥挤度指标 Processor
    
    计算板块拥挤度，识别过热和低估机会。
    """
    
    def __init__(self):
        """初始化 Processor"""
        self.date = None
        self.category = None
        self.top_n = 10
        self.data = []
    
    async def process(self, category: str, date: str, top_n: int = 10) -> dict[str, Any]:
        """处理主流程
        
        Args:
            category: 板块类型（L1/L2/L3/concept）
            date: 日期（YYYY-MM-DD）
            top_n: 返回 Top N 结果
        
        Returns:
            包含拥挤度指标的结果字典
        """
        self.date = date
        self.category = category
        self.top_n = top_n
        
        # 1. 获取数据
        self.data = await self._fetch_data()
        
        # 2. 计算成交额占比
        self._calc_volume_ratio()
        
        # 3. 计算拥挤度指标
        boards = self._calc_crowdedness()
        
        # 4. 按拥挤度排序（降序）
        boards = sorted(boards, key=lambda x: x['crowdedness'], reverse=True)
        
        # 5. 构建结果
        result = {
            "date": date,
            "category": category,
            "weights": CROWDEDNESS_WEIGHTS,
            "boards": boards,
        }
        
        # 6. 保存完整数据
        self._save_output(result)
        
        # 7. 返回精简结果（Top N）
        return {
            "date": date,
            "category": category,
            "boards": boards[:top_n],
        }
    
    async def _fetch_data(self) -> list[dict]:
        """获取板块数据
        
        Returns:
            板块数据列表
        """
        if self.category == "concept":
            return await fetch_concept(self.date)
        else:
            return await fetch_industry(category=self.category, date=self.date)
    
    def _calc_volume_ratio(self) -> None:
        """计算成交额占比
        
        成交额占比 = 板块成交额 / 全市场成交额 × 100%
        """
        # 汇总全市场成交额
        total_amount = sum(
            board['metrics'].get('amount', 0) 
            for board in self.data
        )
        
        # 计算占比
        if total_amount > 0:
            for board in self.data:
                amount = board['metrics'].get('amount', 0)
                board['metrics']['volume_ratio'] = (amount / total_amount) * 100
        else:
            for board in self.data:
                board['metrics']['volume_ratio'] = 0.0
    
    def _calc_crowdedness(self) -> list[dict]:
        """计算拥挤度指标
        
        拥挤度 = 换手率分位 × 50% + 成交额占比分位 × 50%
        
        Returns:
            包含拥挤度指标的板块数据列表
        """
        # 提取各维度数据
        turnover_rates = [board['metrics']['turnover_rate'] for board in self.data]
        volume_ratios = [board['metrics']['volume_ratio'] for board in self.data]
        
        # 计算分位（0-100）
        turnover_percentiles = self._calc_percentile(turnover_rates)
        volume_percentiles = self._calc_percentile(volume_ratios)
        
        # 计算拥挤度
        boards = []
        for i, board in enumerate(self.data):
            turnover_pct = turnover_percentiles[i]
            volume_pct = volume_percentiles[i]
            
            # 计算拥挤度
            crowdedness = (
                turnover_pct * CROWDEDNESS_WEIGHTS["turnover_rate_percentile"] +
                volume_pct * CROWDEDNESS_WEIGHTS["volume_ratio_percentile"]
            )
            
            # 判断拥挤度等级
            level = self._judge_crowdedness_level(crowdedness)
            
            # 构建结果
            boards.append({
                "name": board['name'],
                "code": board['code'],
                "crowdedness": round(crowdedness, 2),
                "level": level,
                "details": {
                    "turnover_rate": round(board['metrics']['turnover_rate'], 2),
                    "turnover_percentile": round(turnover_pct, 2),
                    "volume_ratio": round(board['metrics']['volume_ratio'], 4),
                    "volume_percentile": round(volume_pct, 2),
                },
                "metrics": board['metrics'],
            })
        
        return boards
    
    def _calc_percentile(self, values: list[float]) -> list[float]:
        """计算分位数（0-100）
        
        使用排名法：percentile = (rank - 1) / (n - 1) × 100
        
        Args:
            values: 原始值列表
        
        Returns:
            分位数列表（0-100）
        """
        if not values:
            return []
        
        n = len(values)
        if n == 1:
            return [100.0]  # 只有一个值，视为 100%
        
        # 获取排序后的索引
        sorted_indices = sorted(range(n), key=lambda i: values[i])
        
        # 计算每个值的分位数
        percentiles = [0.0] * n
        for rank, idx in enumerate(sorted_indices):
            # 分位数 = (rank / (n - 1)) × 100
            percentiles[idx] = (rank / (n - 1)) * 100
        
        return percentiles
    
    def _judge_crowdedness_level(self, crowdedness: float) -> str:
        """判断拥挤度等级
        
        Args:
            crowdedness: 拥挤度值（0-100）
        
        Returns:
            拥挤度等级描述
        """
        if crowdedness > CROWDEDNESS_LEVELS["high"][0]:
            return CROWDEDNESS_LEVELS["high"][1]
        elif crowdedness > CROWDEDNESS_LEVELS["medium"][0]:
            return CROWDEDNESS_LEVELS["medium"][1]
        else:
            return CROWDEDNESS_LEVELS["low"][1]
    
    def _save_output(self, result: dict[str, Any]) -> None:
        """保存完整数据到文件
        
        Args:
            result: 完整结果数据
        """
        output_path = get_output_path(
            SKILL_NAME,
            PROCESSOR_NAME,
            self.date,
            ext="json",
        )
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="板块拥挤度指标")
    parser.add_argument(
        "--category",
        choices=["L1", "L2", "L3", "concept"],
        default="L1",
        help="板块类型（L1/L2/L3/concept，默认 L1）",
    )
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="日期（YYYY-MM-DD，默认今天）",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="返回 Top N 结果（默认 10）",
    )
    return parser.parse_args()


async def main():
    """主入口"""
    args = parse_args()
    
    processor = CrowdednessProcessor()
    result = await processor.process(
        category=args.category,
        date=args.date,
        top_n=args.top_n,
    )
    
    # 打印精简结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
