# -*- coding: utf-8 -*-
"""股债性价比（风险溢价）分析处理器"""

import argparse
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional

from openclaw_alpha.core.processor_utils import get_output_path, load_output

# 沪深300指数代码
HS300_CODE = "000300.SH"


class EquityBondRatioProcessor:
    """股债性价比分析处理器

    计算沪深300风险溢价 = 1/PE - 10Y国债收益率
    """

    def __init__(self):
        """初始化"""
        self.skill_name = "market_sentiment"
        self.processor_name = "equity_bond_ratio"

    def _fetch_bond_yield(self, date: str) -> Optional[float]:
        """
        获取10年期国债收益率

        Args:
            date: 日期，格式 YYYY-MM-DD

        Returns:
            10年期国债收益率（%），失败返回 None
        """
        try:
            import akshare as ak

            # 转换日期格式
            date_str = date.replace("-", "")

            # 获取中债国债收益率曲线
            df = ak.bond_china_yield(start_date=date_str, end_date=date_str)

            if df.empty:
                return None

            # 筛选中债国债收益率曲线
            bond_df = df[df["曲线名称"] == "中债国债收益率曲线"]

            if bond_df.empty:
                return None

            # 获取10年期收益率
            yield_10y = bond_df["10年"].iloc[-1]

            return float(yield_10y)

        except Exception as e:
            print(f"获取国债收益率失败: {e}")
            return None

    def _fetch_hs300_pe(self, date: str) -> Optional[float]:
        """
        获取沪深300 PE

        Args:
            date: 日期，格式 YYYY-MM-DD

        Returns:
            沪深300 PE，失败返回 None
        """
        try:
            # 从 index_analysis 的输出读取
            index_data = load_output("index_analysis", "index", date, ext="json")

            if not index_data:
                return None

            # 查找沪深300数据
            for index in index_data.get("indices", []):
                if index.get("code") == HS300_CODE:
                    return index.get("pe")

            return None

        except Exception as e:
            print(f"获取沪深300 PE失败: {e}")
            return None

    def _fetch_hs300_pe_history(
        self, start_date: str, end_date: str
    ) -> list[dict]:
        """
        获取沪深300 PE 历史数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            历史数据列表
        """
        try:
            # 从 Tushare 获取历史数据
            import os

            import tushare as ts

            token = os.environ.get("TUSHARE_TOKEN")
            if not token:
                print("未找到 TUSHARE_TOKEN")
                return []

            pro = ts.pro_api(token)

            df = pro.index_dailybasic(
                ts_code=HS300_CODE,
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                fields="trade_date,pe",
            )

            if df.empty:
                return []

            result = []
            for _, row in df.iterrows():
                result.append({
                    "date": row["trade_date"][:4] + "-" + row["trade_date"][4:6] + "-" + row["trade_date"][6:],
                    "pe": float(row["pe"]),
                })

            return result

        except Exception as e:
            print(f"获取沪深300 PE历史数据失败: {e}")
            return []

    def _fetch_bond_yield_history(
        self, start_date: str, end_date: str
    ) -> list[dict]:
        """
        获取10年期国债收益率历史数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            历史数据列表
        """
        try:
            import akshare as ak

            df = ak.bond_china_yield(
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
            )

            if df.empty:
                return []

            # 筛选中债国债收益率曲线
            bond_df = df[df["曲线名称"] == "中债国债收益率曲线"]

            if bond_df.empty:
                return []

            result = []
            for _, row in bond_df.iterrows():
                date_str = str(row["日期"])
                if len(date_str) == 10:  # YYYY-MM-DD
                    date_fmt = date_str
                else:
                    date_fmt = date_str[:4] + "-" + date_str[4:6] + "-" + date_str[6:8]

                result.append({
                    "date": date_fmt,
                    "yield_10y": float(row["10年"]),
                })

            return result

        except Exception as e:
            print(f"获取国债收益率历史数据失败: {e}")
            return []

    def _calc_risk_premium(self, pe: float, bond_yield: float) -> float:
        """
        计算风险溢价

        Args:
            pe: 沪深300 PE
            bond_yield: 10年期国债收益率（%）

        Returns:
            风险溢价（%）
        """
        # PE 倒数 * 100 转换为百分比
        equity_yield = 100 / pe
        return equity_yield - bond_yield

    def _calc_percentile(self, value: float, history: list[float]) -> float:
        """
        计算历史分位数

        Args:
            value: 当前值
            history: 历史值列表

        Returns:
            分位数（0-100）
        """
        if not history:
            return 50

        count = sum(1 for h in history if h <= value)
        return round(count / len(history) * 100, 1)

    def _determine_signal(self, percentile: float) -> dict:
        """
        判断择时信号

        Args:
            percentile: 历史分位数

        Returns:
            择时信号
        """
        if percentile >= 80:
            return {
                "signal": "强买入",
                "description": f"风险溢价处于历史高位（{percentile}%分位），股票估值极具吸引力",
            }
        elif percentile >= 60:
            return {
                "signal": "买入",
                "description": f"风险溢价较高（{percentile}%分位），股票相对便宜",
            }
        elif percentile <= 20:
            return {
                "signal": "强卖出",
                "description": f"风险溢价处于历史低位（{percentile}%分位），股票估值昂贵",
            }
        elif percentile <= 40:
            return {
                "signal": "卖出",
                "description": f"风险溢价较低（{percentile}%分位），股票相对昂贵",
            }
        else:
            return {
                "signal": "持有",
                "description": f"风险溢价适中（{percentile}%分位），正常配置",
            }

    def _generate_recommendation(
        self,
        risk_premium: float,
        percentile: float,
        signal: dict,
    ) -> str:
        """
        生成投资建议

        Args:
            risk_premium: 风险溢价
            percentile: 历史分位数
            signal: 择时信号

        Returns:
            投资建议
        """
        recommendations = [signal["description"]]

        if percentile >= 70:
            recommendations.append("建议增加股票仓位，债券可适当降低")
        elif percentile <= 30:
            recommendations.append("建议降低股票仓位，增加债券或现金")
        else:
            recommendations.append("保持当前股债配置比例")

        return "；".join(recommendations)

    async def process(
        self,
        date: str = None,
        lookback_days: int = 252,
    ) -> dict:
        """
        处理股债性价比分析

        Args:
            date: 日期，格式 YYYY-MM-DD
            lookback_days: 回溯天数（用于计算历史分位数）

        Returns:
            股债性价比分析结果
        """
        date = date or datetime.now().strftime("%Y-%m-%d")

        # 1. 获取当日沪深300 PE
        pe = self._fetch_hs300_pe(date)

        if pe is None:
            # 尝试从 Tushare 直接获取
            try:
                import os

                import tushare as ts

                token = os.environ.get("TUSHARE_TOKEN")
                if token:
                    pro = ts.pro_api(token)
                    df = pro.index_dailybasic(
                        ts_code=HS300_CODE,
                        trade_date=date.replace("-", ""),
                        fields="pe",
                    )
                    if not df.empty:
                        pe = float(df["pe"].iloc[0])
            except Exception as e:
                return {
                    "date": date,
                    "error": f"获取沪深300 PE失败: {e}",
                }

        if pe is None:
            return {
                "date": date,
                "error": "获取沪深300 PE失败",
            }

        # 2. 获取当日10年期国债收益率
        bond_yield = self._fetch_bond_yield(date)

        if bond_yield is None:
            return {
                "date": date,
                "error": "获取10年期国债收益率失败",
            }

        # 3. 计算风险溢价
        risk_premium = self._calc_risk_premium(pe, bond_yield)

        # 4. 获取历史数据计算分位数
        end_date_obj = datetime.strptime(date, "%Y-%m-%d")
        start_date = (end_date_obj - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

        pe_history = self._fetch_hs300_pe_history(start_date, date)
        bond_history = self._fetch_bond_yield_history(start_date, date)

        # 计算历史风险溢价
        risk_premium_history = []

        if pe_history and bond_history:
            # 按日期匹配
            bond_dict = {b["date"]: b["yield_10y"] for b in bond_history}

            for pe_item in pe_history:
                pe_date = pe_item["date"]
                if pe_date in bond_dict:
                    rp = self._calc_risk_premium(pe_item["pe"], bond_dict[pe_date])
                    risk_premium_history.append(rp)

        # 5. 计算分位数
        percentile = self._calc_percentile(risk_premium, risk_premium_history)

        # 6. 判断信号
        signal = self._determine_signal(percentile)
        recommendation = self._generate_recommendation(risk_premium, percentile, signal)

        # 7. 构建结果
        result = {
            "date": date,
            "hs300_pe": round(pe, 2),
            "equity_yield": round(100 / pe, 2),
            "bond_yield_10y": round(bond_yield, 2),
            "risk_premium": round(risk_premium, 2),
            "percentile": percentile,
            "signal": signal,
            "recommendation": recommendation,
            "sample_count": len(risk_premium_history),
        }

        # 8. 保存完整数据到文件
        output_path = get_output_path(
            self.skill_name, self.processor_name, date, ext="json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="股债性价比分析")
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="分析日期，格式 YYYY-MM-DD，默认今天",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=252,
        help="回溯天数，用于计算历史分位数，默认 252（一年）",
    )
    return parser.parse_args()


async def main():
    """主入口"""
    args = parse_args()
    processor = EquityBondRatioProcessor()
    result = await processor.process(date=args.date, lookback_days=args.lookback_days)

    # 输出精简结果
    output = {
        "date": result["date"],
        "hs300_pe": result.get("hs300_pe"),
        "risk_premium": result.get("risk_premium"),
        "percentile": result.get("percentile"),
        "signal": result.get("signal", {}).get("signal"),
        "recommendation": result.get("recommendation"),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
