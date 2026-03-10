# -*- coding: utf-8 -*-
"""行业信息 Fetcher - Tushare 实现"""

import asyncio
import logging
from typing import Any

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.exceptions import NetworkError, RateLimitError, ServerError
from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.data_sources import registry

logger = logging.getLogger(__name__)


class IndustryInfoFetcherTushare(FetchMethod):
    """Tushare 实现

    使用 Tushare stock_basic 接口获取股票行业信息。
    """

    name = "industry_info_tushare"
    required_data_source = "tushare"
    required_credit = 2000  # stock_basic 需要 2000 积分
    priority = 20  # 优先级高于 AKShare

    def __init__(self):
        """初始化"""
        super().__init__()
        # 延迟导入避免循环依赖
        from .industry_fetcher import get_fetcher

        # 注册到 Fetcher 单例
        fetcher = get_fetcher()
        fetcher.register(self, self.priority)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    async def _call_api(self, codes: list[str]) -> pd.DataFrame:
        """
        调用 Tushare API 批量获取股票基础信息

        Args:
            codes: 股票代码列表（6位数字）

        Returns:
            原始 DataFrame

        Raises:
            NetworkError: 网络错误
            RateLimitError: 限流
            ServerError: 服务端错误
        """
        try:
            tushare_ds = registry.get("tushare")
            pro = await tushare_ds.get_client()

            # 转换代码格式：000001 -> 000001.SZ
            ts_codes = [self._convert_code(code) for code in codes]

            # 批量查询（一次最多 100 个）
            dfs = []
            for i in range(0, len(ts_codes), 100):
                chunk = ts_codes[i : i + 100]
                ts_codes_str = ",".join(chunk)
                df = await asyncio.to_thread(
                    pro.stock_basic,
                    ts_code=ts_codes_str,
                    fields="ts_code,symbol,name,industry",
                )
                if not df.empty:
                    dfs.append(df)

            if not dfs:
                return pd.DataFrame()

            return pd.concat(dfs, ignore_index=True)

        except Exception as e:
            error_msg = str(e).lower()
            if "rate" in error_msg or "limit" in error_msg or "429" in error_msg:
                raise RateLimitError(f"Tushare 限流: {e}")
            elif "timeout" in error_msg or "connection" in error_msg:
                raise NetworkError(f"网络错误: {e}")
            elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                raise ServerError(f"服务端错误: {e}")
            else:
                raise

    def _convert_code(self, symbol: str) -> str:
        """转换股票代码格式

        Args:
            symbol: 6 位股票代码（如 "000001"）

        Returns:
            Tushare 格式代码（如 "000001.SZ"）
        """
        if "." in symbol:
            return symbol

        # 根据代码前缀判断市场
        if symbol.startswith(("60", "68")):
            return f"{symbol}.SH"
        elif symbol.startswith(("00", "30")):
            return f"{symbol}.SZ"
        elif symbol.startswith(("688", "689")):
            return f"{symbol}.SH"
        else:
            # 默认深圳
            return f"{symbol}.SZ"

    def _parse_data(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        解析股票基础信息

        Args:
            df: 原始 DataFrame

        Returns:
            代码到行业信息的映射
        """
        from .industry_fetcher import IndustryInfo

        result = {}

        if df is None or df.empty:
            return result

        for _, row in df.iterrows():
            try:
                symbol = str(row.get("symbol", ""))
                if not symbol:
                    continue

                result[symbol] = IndustryInfo(
                    code=symbol,
                    name=str(row.get("name", "")),
                    industry=str(row.get("industry", "未知")),
                )
            except Exception as e:
                logger.warning(f"解析股票行业信息失败: {e}")
                continue

        return result

    async def fetch(self, codes: list[str]) -> dict[str, Any]:
        """
        获取多只股票的行业信息

        Args:
            codes: 股票代码列表

        Returns:
            代码到行业信息的映射
        """
        raw_data = await self._call_api(codes)
        return self._parse_data(raw_data)


# 自动注册（仅当作为模块导入时）
if __name__ != "__main__":
    _instance = IndustryInfoFetcherTushare()


# 调试入口
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到路径
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    skills_dir = project_root / "skills"
    if str(skills_dir) not in sys.path:
        sys.path.insert(0, str(skills_dir))

    async def test():
        fetcher = IndustryInfoFetcherTushare()
        codes = ["000001", "600000", "002475"]
        print(f"正在获取 {len(codes)} 只股票的行业信息...")
        result = await fetcher.fetch(codes)
        for code, info in result.items():
            print(f"  {code} {info.name}: {info.industry}")

    asyncio.run(test())
