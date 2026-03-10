# -*- coding: utf-8 -*-
"""行业信息 Fetcher - AKShare 实现"""

import asyncio
import logging
from typing import Any

import akshare as ak
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from openclaw_alpha.core.exceptions import NetworkError, RateLimitError, ServerError
from openclaw_alpha.core.fetcher import FetchMethod

logger = logging.getLogger(__name__)


class IndustryInfoFetcherAkshare(FetchMethod):
    """AKShare 实现"""

    name = "industry_info_akshare"
    required_data_source = "akshare"
    priority = 10

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
    async def _call_api(self, code: str) -> pd.DataFrame:
        """
        调用 AKShare API 获取个股信息

        Args:
            code: 股票代码（6位数字）

        Returns:
            原始 DataFrame

        Raises:
            NetworkError: 网络错误
            RateLimitError: 限流
            ServerError: 服务端错误
        """
        try:
            df = await asyncio.to_thread(ak.stock_individual_info_em, symbol=code)
            return df
        except Exception as e:
            error_msg = str(e).lower()
            if "rate" in error_msg or "limit" in error_msg or "429" in error_msg:
                raise RateLimitError(f"AKShare 限流: {e}")
            elif "timeout" in error_msg or "connection" in error_msg:
                raise NetworkError(f"网络错误: {e}")
            elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                raise ServerError(f"服务端错误: {e}")
            else:
                raise

    def _parse_info(self, df: pd.DataFrame, code: str):
        """
        解析个股信息

        Args:
            df: 原始 DataFrame
            code: 股票代码

        Returns:
            IndustryInfo 或 None
        """
        from .industry_fetcher import IndustryInfo

        if df is None or df.empty:
            return None

        try:
            # 将 item-value 转换为字典
            info_dict = dict(zip(df["item"], df["value"]))

            return IndustryInfo(
                code=code,
                name=str(info_dict.get("股票简称", "")),
                industry=str(info_dict.get("行业", "未知")),
            )
        except Exception as e:
            logger.warning(f"解析股票 {code} 行业信息失败: {e}")
            return None

    async def fetch(self, codes: list[str]) -> dict[str, Any]:
        """
        获取多只股票的行业信息

        Args:
            codes: 股票代码列表

        Returns:
            代码到行业信息的映射
        """
        result = {}

        # 批量获取，每次间隔避免限流
        for i, code in enumerate(codes):
            try:
                df = await self._call_api(code)
                info = self._parse_info(df, code)
                if info:
                    result[code] = info

                # 避免频繁请求
                if i < len(codes) - 1:
                    await asyncio.sleep(0.3)

            except Exception as e:
                logger.warning(f"获取股票 {code} 行业信息失败: {e}")
                continue

        return result


# 自动注册（仅当作为模块导入时）
if __name__ != "__main__":
    _instance = IndustryInfoFetcherAkshare()


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
        fetcher = IndustryInfoFetcherAkshare()
        codes = ["000001", "600000", "002475"]
        print(f"正在获取 {len(codes)} 只股票的行业信息...")
        result = await fetcher.fetch(codes)
        for code, info in result.items():
            print(f"  {code} {info.name}: {info.industry}")

    asyncio.run(test())
