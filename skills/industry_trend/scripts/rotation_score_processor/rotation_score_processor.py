# -*- coding: utf-8 -*-
"""行业轮动综合评分 Processor"""

import argparse
import asyncio
import json
from datetime import datetime
from typing import Any

from openclaw_alpha.core.processor_utils import get_output_path, load_output

# 导入数据源模块以触发注册
from openclaw_alpha.data_sources import registry  # noqa: F401



# 常量定义
SKILL_NAME = "industry-trend"
PROCESSOR_NAME = "rotation-score"

# 评分等级阈值
SCORE_LEVELS = {
    "A+": (70, "黄金机会"),
    "A": (50, "优质机会"),
    "B": (30, "一般机会"),
    "C": (0, "风险机会"),
}

# 黄金组合阈值
GOLDEN_COMBO = {
    "heat_threshold": 60,     # 热度阈值
    "crowdedness_threshold": 40,  # 拥挤度阈值
}


class RotationScoreProcessor:
    """行业轮动综合评分 Processor
    
    计算轮动评分，识别黄金组合机会。
    """
    
    def __init__(self):
        """初始化 Processor"""
        self.date = None
        self.category = None
        self.top_n = 10
        self.heat_data = None
        self.crowdedness_data = None
    
    async def process(self, category: str, date: str, top_n: int = 10) -> dict[str, Any]:
        """处理主流程
        
        Args:
            category: 板块类型（L1/L2/L3/concept）
            date: 日期（YYYY-MM-DD）
            top_n: 返回 Top N 结果
        
        Returns:
            包含轮动评分的结果字典
        """
        self.date = date
        self.category = category
        self.top_n = top_n
        
        # 1. 获取热度和拥挤度数据
        await self._load_or_fetch_data()
        
        if not self.heat_data or not self.crowdedness_data:
            return {
                "date": date,
                "category": category,
                "error": "无法获取热度或拥挤度数据",
                "boards": [],
            }
        
        # 2. 合并数据并计算轮动评分
        boards = self._calc_rotation_score()
        
        # 3. 按轮动评分排序（降序）
        boards = sorted(boards, key=lambda x: x['rotation_score'], reverse=True)
        
        # 4. 构建结果
        result = {
            "date": date,
            "category": category,
            "golden_combo_thresholds": GOLDEN_COMBO,
            "boards": boards,
        }
        
        # 5. 保存完整数据
        self._save_output(result)
        
        # 6. 返回精简结果（Top N）
        return {
            "date": date,
            "category": category,
            "boards": boards[:top_n],
        }
    
    async def _load_or_fetch_data(self) -> None:
        """加载或获取热度和拥挤度数据"""
        # 尝试从文件加载热度数据
        heat_data = load_output(SKILL_NAME, "heat", self.date, ext="json")
        
        if heat_data:
            self.heat_data = heat_data
        else:
            # 需要先计算热度
            self.heat_data = await self._fetch_and_calc_heat()
        
        # 尝试从文件加载拥挤度数据
        crowdedness_data = load_output(SKILL_NAME, "crowdedness", self.date, ext="json")
        
        if crowdedness_data:
            self.crowdedness_data = crowdedness_data
        else:
            # 需要先计算拥挤度
            self.crowdedness_data = await self._fetch_and_calc_crowdedness()
    
    async def _fetch_and_calc_heat(self) -> dict | None:
        """获取并计算热度数据"""
        from skills.industry_trend.scripts.industry_trend_processor.industry_trend_processor import IndustryTrendProcessor
        
        processor = IndustryTrendProcessor()
        await processor.process(
            category=self.category,
            date=self.date,
            top_n=1000,  # 获取所有数据
        )
        
        # 重新加载保存的数据
        return load_output(SKILL_NAME, "heat", self.date, ext="json")
    
    async def _fetch_and_calc_crowdedness(self) -> dict | None:
        """获取并计算拥挤度数据"""
        from skills.industry_trend.scripts.crowdedness_processor.crowdedness_processor import CrowdednessProcessor
        
        processor = CrowdednessProcessor()
        await processor.process(
            category=self.category,
            date=self.date,
            top_n=1000,  # 获取所有数据
        )
        
        # 重新加载保存的数据
        return load_output(SKILL_NAME, "crowdedness", self.date, ext="json")
    
    def _calc_rotation_score(self) -> list[dict]:
        """计算轮动评分
        
        轮动评分 = 热度指数 × (100 - 拥挤度) / 100
        
        Returns:
            包含轮动评分的板块数据列表
        """
        # 构建拥挤度映射
        crowdedness_map = {
            board['name']: board['crowdedness']
            for board in self.crowdedness_data.get('boards', [])
        }
        
        boards = []
        heat_boards = self.heat_data.get('boards', [])
        
        for heat_board in heat_boards:
            name = heat_board['name']
            heat_index = heat_board.get('heat_index', 0)
            crowdedness = crowdedness_map.get(name, 50)  # 默认中等拥挤度
            
            # 计算轮动评分
            rotation_score = heat_index * (100 - crowdedness) / 100
            
            # 判断评分等级
            level = self._judge_score_level(rotation_score)
            
            # 判断是否黄金组合
            is_golden = (
                heat_index > GOLDEN_COMBO["heat_threshold"] and
                crowdedness < GOLDEN_COMBO["crowdedness_threshold"]
            )
            
            boards.append({
                "name": name,
                "code": heat_board.get('code', ''),
                "rotation_score": round(rotation_score, 2),
                "level": level,
                "is_golden": is_golden,
                "details": {
                    "heat_index": heat_index,
                    "crowdedness": crowdedness,
                    "trend": heat_board.get('trend', ''),
                    "pct_change": heat_board['metrics'].get('pct_change', 0),
                },
            })
        
        return boards
    
    def _judge_score_level(self, score: float) -> str:
        """判断评分等级
        
        Args:
            score: 轮动评分（0-100）
        
        Returns:
            评分等级描述
        """
        if score > SCORE_LEVELS["A+"][0]:
            return SCORE_LEVELS["A+"][1]
        elif score > SCORE_LEVELS["A"][0]:
            return SCORE_LEVELS["A"][1]
        elif score > SCORE_LEVELS["B"][0]:
            return SCORE_LEVELS["B"][1]
        else:
            return SCORE_LEVELS["C"][1]
    
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
    parser = argparse.ArgumentParser(description="行业轮动综合评分")
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
    
    processor = RotationScoreProcessor()
    result = await processor.process(
        category=args.category,
        date=args.date,
        top_n=args.top_n,
    )
    
    # 打印精简结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
