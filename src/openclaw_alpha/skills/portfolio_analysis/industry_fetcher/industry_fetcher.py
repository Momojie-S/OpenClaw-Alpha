# -*- coding: utf-8 -*-
"""行业信息 Fetcher 入口"""

from dataclasses import dataclass

from openclaw_alpha.core.exceptions import NoAvailableMethodError
from openclaw_alpha.core.fetcher import Fetcher


@dataclass
class IndustryInfo:
    """行业信息"""

    code: str
    name: str
    industry: str


class IndustryInfoFetcher(Fetcher):
    """行业信息 Fetcher 入口"""

    name = "industry_info"

    async def fetch(self, codes: list[str]) -> dict[str, IndustryInfo]:
        """
        获取多只股票的行业信息

        Args:
            codes: 股票代码列表（6位数字）

        Returns:
            代码到行业信息的映射，获取失败的股票不会出现在结果中
        """
        method, errors = self._select_available()
        if method is None:
            checked_methods = [
                f"{m.name}(ds={m.required_data_source}, credit={m.required_credit})"
                for m in self._methods
            ]
            raise NoAvailableMethodError(self.name, checked_methods, errors)
        return await method.fetch(codes)


# 单例实例
_fetcher: IndustryInfoFetcher | None = None


def get_fetcher() -> IndustryInfoFetcher:
    """获取 Fetcher 单例"""
    global _fetcher
    if _fetcher is None:
        _fetcher = IndustryInfoFetcher()
    return _fetcher


async def fetch(codes: list[str]) -> dict[str, IndustryInfo]:
    """获取行业信息（便捷函数）"""
    return await get_fetcher().fetch(codes)
