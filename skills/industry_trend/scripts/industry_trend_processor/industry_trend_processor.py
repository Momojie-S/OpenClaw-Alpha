# -*- coding: utf-8 -*-
"""产业热度追踪 Processor"""

import argparse
import asyncio
import json
from datetime import datetime
from typing import Any

from openclaw_alpha.core.processor_utils import get_output_path
# 导入数据源模块以触发注册
from openclaw_alpha.data_sources import registry  # noqa: F401

from skills.industry_trend.scripts.industry_fetcher import fetch as fetch_industry
from skills.industry_trend.scripts.concept_fetcher import fetch as fetch_concept


# 常量定义
SKILL_NAME = "industry-trend"
PROCESSOR_NAME = "heat"

# 热度指数权重（申万行业 - 无涨跌家数）
INDUSTRY_WEIGHTS = {
    "pct_change": 0.35,      # 涨跌幅
    "turnover_rate": 0.30,   # 换手率
    "volume_ratio": 0.35,    # 成交额占比
}

# 热度指数权重（概念板块 - 有涨跌家数）
CONCEPT_WEIGHTS = {
    "pct_change": 0.30,      # 涨跌幅
    "turnover_rate": 0.25,   # 换手率
    "volume_ratio": 0.25,    # 成交额占比
    "up_ratio": 0.20,        # 涨跌家数比
}


class IndustryTrendProcessor:
    """产业热度追踪 Processor
    
    计算板块热度指数，识别市场热点和趋势变化。
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
            包含热度排名的结果字典
        """
        self.date = date
        self.category = category
        self.top_n = top_n
        
        # 1. 获取数据
        self.data = await self._fetch_data()
        
        # 2. 计算成交额占比
        self._calc_volume_ratio()
        
        # 3. 计算热度指数
        boards = self._calc_heat_index()
        
        # 4. 判断趋势信号
        boards = self._judge_trend(boards)
        
        # 5. 按热度排序
        boards = sorted(boards, key=lambda x: x['heat_index'], reverse=True)
        
        # 6. 构建结果
        result = {
            "date": date,
            "category": category,
            "weights": INDUSTRY_WEIGHTS if category != "concept" else CONCEPT_WEIGHTS,
            "boards": boards,
        }
        
        # 7. 保存完整数据
        self._save_output(result)
        
        # 8. 返回精简结果（Top N）
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
    
    def _calc_heat_index(self) -> list[dict]:
        """计算热度指数
        
        Returns:
            包含热度指数的板块数据列表
        """
        # 提取各维度数据
        pct_changes = [board['metrics']['pct_change'] for board in self.data]
        turnover_rates = [board['metrics']['turnover_rate'] for board in self.data]
        volume_ratios = [board['metrics']['volume_ratio'] for board in self.data]
        
        # 归一化
        pct_change_norm = self._normalize(pct_changes)
        turnover_norm = self._normalize(turnover_rates)
        volume_ratio_norm = self._normalize(volume_ratios)
        
        # 选择权重
        weights = INDUSTRY_WEIGHTS if self.category != "concept" else CONCEPT_WEIGHTS
        
        # 计算热度指数
        boards = []
        for i, board in enumerate(self.data):
            # 计算各维度得分
            scores = {
                "pct_change": pct_change_norm[i] * weights["pct_change"],
                "turnover_rate": turnover_norm[i] * weights["turnover_rate"],
                "volume_ratio": volume_ratio_norm[i] * weights["volume_ratio"],
            }
            
            # 概念板块加入涨跌家数比
            if self.category == "concept":
                up_count = board['metrics'].get('up_count', 0)
                down_count = board['metrics'].get('down_count', 0)
                total_count = up_count + down_count
                
                if total_count > 0:
                    up_ratio = (up_count / total_count) * 100
                else:
                    up_ratio = 0.0
                
                board['metrics']['up_ratio'] = up_ratio
                
                # 归一化涨跌家数比（0-100 已经是归一化的）
                scores["up_ratio"] = up_ratio * weights["up_ratio"]
            
            # 计算总热度指数
            heat_index = sum(scores.values())
            
            # 构建结果
            boards.append({
                **board,
                'heat_index': round(heat_index, 2),
                'scores': {k: round(v, 2) for k, v in scores.items()},
            })
        
        return boards
    
    def _normalize(self, values: list[float]) -> list[float]:
        """Min-Max 归一化
        
        Args:
            values: 原始值列表
        
        Returns:
            归一化后的值列表（0-100）
        """
        if not values:
            return []
        
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            return [50.0] * len(values)  # 所有值相同，返回中间值
        
        return [
            (v - min_val) / (max_val - min_val) * 100
            for v in values
        ]
    
    def _judge_trend(self, boards: list[dict]) -> list[dict]:
        """判断趋势信号
        
        Args:
            boards: 板块数据列表
        
        Returns:
            包含趋势信号的板块数据列表
        """
        # 加载上一交易日数据
        prev_data = self._load_previous_data()
        prev_heat_map = {}
        if prev_data:
            prev_heat_map = {
                board['name']: board['heat_index']
                for board in prev_data.get('boards', [])
            }
        
        for board in boards:
            pct_change = board['metrics']['pct_change']
            heat_index = board['heat_index']
            board_name = board['name']
            
            # 计算热度环比
            prev_heat = prev_heat_map.get(board_name)
            if prev_heat is not None and prev_heat > 0:
                heat_change = (heat_index - prev_heat) / prev_heat * 100
            else:
                heat_change = None  # 无历史数据
            
            # 判断趋势
            if heat_change is None:
                # 无历史数据
                if pct_change < -3:
                    trend = "降温中"
                else:
                    trend = "新"
            elif heat_change > 20 and pct_change > 0:
                trend = "加热中"
            elif heat_change < -20 or pct_change < -3:
                trend = "降温中"
            else:
                trend = "稳定"
            
            board['trend'] = trend
            board['heat_change'] = round(heat_change, 2) if heat_change is not None else None
        
        return boards
    
    def _load_previous_data(self) -> dict | None:
        """加载上一交易日的数据文件
        
        Returns:
            上一交易日数据，不存在则返回 None
        """
        from datetime import timedelta
        
        # 解析当前日期
        if not self.date:
            return None
        
        try:
            current_date = datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError:
            return None
        
        # 最多回溯 5 天寻找有效数据文件
        for i in range(1, 6):
            prev_date = (current_date - timedelta(days=i)).strftime("%Y-%m-%d")
            prev_path = get_output_path(
                SKILL_NAME,
                PROCESSOR_NAME,
                prev_date,
                ext="json",
            )
            
            if prev_path.exists():
                try:
                    with open(prev_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError):
                    continue
        
        return None
    
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
    parser = argparse.ArgumentParser(description="产业热度追踪")
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
    
    processor = IndustryTrendProcessor()
    result = await processor.process(
        category=args.category,
        date=args.date,
        top_n=args.top_n,
    )
    
    # 打印精简结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
