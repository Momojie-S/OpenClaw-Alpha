# -*- coding: utf-8 -*-
"""持仓相关性数据获取器

获取多只股票的历史价格数据，用于计算相关系数矩阵。
"""

import asyncio
import logging

import akshare as ak
import pandas as pd

from openclaw_alpha.core.fetcher import Fetcher, FetchMethod
# 导入数据源以触发注册
from openclaw_alpha.data_sources import AkshareDataSource  # noqa: F401

logger = logging.getLogger(__name__)


class CorrelationFetcherAkshare(FetchMethod):
    """AKShare 实现 - 获取股票历史价格"""

    name = "correlation_akshare"
    required_data_source = "akshare"
    priority = 10

    async def fetch(
        self,
        codes: list[str],
        days: int = 60,
        adjust: str = "qfq",
    ) -> dict[str, pd.DataFrame]:
        """
        获取多只股票的历史价格数据

        Args:
            codes: 股票代码列表（如 ["000001", "600000"]）
            days: 历史天数（默认 60 天）
            adjust: 复权类型（qfq=前复权, hfq=后复权, 空=不复权）

        Returns:
            字典：{股票代码: DataFrame}，DataFrame 包含日期、收盘价等

        Raises:
            ValueError: 参数错误
            RuntimeError: 数据获取失败
        """
        if not codes:
            raise ValueError(
                "参数 codes 不能为空。"
                "请提供至少一个股票代码，例如：['000001', '600000']"
            )

        if len(codes) > 20:
            logger.warning(f"股票数量过多（{len(codes)}），可能耗时较长")

        logger.info(f"开始获取 {len(codes)} 只股票的历史价格，天数={days}")

        # 并发获取所有股票数据
        tasks = [self._fetch_single(code, days, adjust) for code in codes]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 整理结果
        data = {}
        failed = []

        for code, result in zip(codes, results):
            if isinstance(result, Exception):
                logger.error(f"获取 {code} 失败: {result}")
                failed.append(code)
            elif isinstance(result, pd.DataFrame) and not result.empty:
                data[code] = result
            else:
                logger.warning(f"获取 {code} 数据为空")
                failed.append(code)

        if failed:
            logger.warning(f"获取失败的股票: {failed}")

        if not data:
            raise RuntimeError(
                f"所有股票数据获取失败（共 {len(codes)} 只）。"
                f"请检查股票代码是否正确，或检查网络连接后重试"
            )

        logger.info(f"成功获取 {len(data)} 只股票的历史价格")
        return data

    async def _fetch_single(
        self,
        code: str,
        days: int,
        adjust: str,
    ) -> pd.DataFrame:
        """
        获取单只股票的历史价格

        Args:
            code: 股票代码
            days: 历史天数
            adjust: 复权类型

        Returns:
            DataFrame，包含日期、收盘价
        """
        try:
            # 使用 AKShare 获取股票历史数据
            # ak.stock_zh_a_hist 返回 DataFrame
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                adjust=adjust,
            )

            if df.empty:
                return pd.DataFrame()

            # 只保留需要的列
            df = df[["日期", "收盘"]].copy()
            df.columns = ["date", "close"]
            df["date"] = pd.to_datetime(df["date"])

            # 按日期排序，取最近 days 天
            df = df.sort_values("date").tail(days)

            # 重置索引
            df = df.reset_index(drop=True)

            return df

        except Exception as e:
            logger.error(f"获取 {code} 历史数据异常: {e}")
            raise


class CorrelationFetcher(Fetcher):
    """持仓相关性数据获取器（入口）"""

    name = "correlation_fetcher"

    def __init__(self) -> None:
        super().__init__()
        # 注册 AKShare 实现
        self.register(CorrelationFetcherAkshare())


# 全局实例
_fetcher: CorrelationFetcher | None = None


def get_fetcher() -> CorrelationFetcher:
    """获取全局 Fetcher 实例"""
    global _fetcher
    if _fetcher is None:
        _fetcher = CorrelationFetcher()
    return _fetcher


async def fetch(
    codes: list[str],
    days: int = 60,
    adjust: str = "qfq",
) -> dict[str, pd.DataFrame]:
    """
    获取多只股票的历史价格数据（便捷函数）

    Args:
        codes: 股票代码列表
        days: 历史天数（默认 60 天）
        adjust: 复权类型（qfq=前复权）

    Returns:
        字典：{股票代码: DataFrame}
    """
    fetcher = get_fetcher()
    return await fetcher.fetch(codes, days, adjust)


# 命令行入口（用于调试）
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python correlation_fetcher.py 000001,600000 [days]")
        sys.exit(1)

    codes = sys.argv[1].split(",")
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 60

    async def main():
        data = await fetch(codes, days)
        for code, df in data.items():
            print(f"\n{code} - {len(df)} 条记录")
            print(df.tail())

    asyncio.run(main())
