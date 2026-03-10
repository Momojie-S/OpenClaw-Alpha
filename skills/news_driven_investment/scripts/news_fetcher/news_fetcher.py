# -*- coding: utf-8 -*-
"""新闻数据获取 Fetcher

从 AKShare 获取财经新闻数据，支持关键词和日期筛选。
"""

import asyncio
from typing import Optional
from dataclasses import dataclass, field

import akshare as ak

from openclaw_alpha.core.fetcher import Fetcher, FetchMethod


@dataclass
class NewsItem:
    """新闻条目"""
    title: str
    content: str
    date: str
    time: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None


@dataclass
class NewsResult:
    """新闻获取结果"""
    news: list[NewsItem] = field(default_factory=list)
    total: int = 0
    source: str = ""


class NewsFetcherCls(Fetcher):
    """新闻数据 Fetcher 入口类"""
    
    name = "news"
    
    def __init__(self):
        super().__init__()
        # 注册实现（按优先级）
        self.register(NewsFetcherAkshare(), priority=10)
    
    async def fetch(
        self,
        source: str = "cls_global",
        symbol: Optional[str] = None,
        keyword: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 20
    ) -> NewsResult:
        """获取新闻数据
        
        Args:
            source: 新闻源
                - "cls_global": 财联社全球资讯（默认）
                - "cls_important": 财联社重点资讯
                - "stock": 个股新闻（需指定 symbol）
            symbol: 股票代码（仅 source="stock" 时使用）
            keyword: 关键词筛选（在标题和内容中匹配）
            date: 日期筛选（YYYY-MM-DD 格式）
            limit: 返回数量限制
        
        Returns:
            NewsResult: 新闻结果
        """
        return await super().fetch(
            source=source,
            symbol=symbol,
            keyword=keyword,
            date=date,
            limit=limit
        )


class NewsFetcherAkshare(FetchMethod):
    """AKShare 新闻数据获取实现"""
    
    name = "news_akshare"
    required_data_source = "akshare"
    priority = 10
    
    async def fetch(
        self,
        source: str = "cls_global",
        symbol: Optional[str] = None,
        keyword: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 20
    ) -> NewsResult:
        """从 AKShare 获取新闻并筛选"""
        
        # 获取原始新闻数据（多获取一些以便筛选）
        fetch_limit = limit * 5 if keyword or date else limit
        
        if source == "cls_global":
            result = await self._fetch_cls_news(symbol="全部", limit=fetch_limit)
        elif source == "cls_important":
            result = await self._fetch_cls_news(symbol="重点", limit=fetch_limit)
        elif source == "stock":
            if not symbol:
                raise ValueError(
                    "参数 symbol 缺失（必填）。"
                    "个股新闻必须指定股票代码，例如：--symbol 000001"
                )
            result = await self._fetch_stock_news(symbol=symbol, limit=fetch_limit)
        else:
            raise ValueError(
                f"参数 source '{source}' 不存在（收到 '{source}'）。"
                f"可用来源：cls_global（财联社全球）、cls_important（财联社重点）、stock（个股新闻）"
            )
        
        # 应用筛选
        filtered_news = self._filter_news(result.news, keyword=keyword, date=date)
        
        # 限制数量
        filtered_news = filtered_news[:limit]
        
        return NewsResult(
            news=filtered_news,
            total=len(filtered_news),
            source=result.source
        )
    
    def _filter_news(
        self,
        news: list[NewsItem],
        keyword: Optional[str] = None,
        date: Optional[str] = None
    ) -> list[NewsItem]:
        """筛选新闻
        
        Args:
            news: 原始新闻列表
            keyword: 关键词（在标题和内容中匹配）
            date: 日期（YYYY-MM-DD 格式）
        
        Returns:
            筛选后的新闻列表
        """
        result = news
        
        # 关键词筛选
        if keyword:
            keyword_lower = keyword.lower()
            result = [
                item for item in result
                if keyword_lower in item.title.lower() 
                or keyword_lower in item.content.lower()
            ]
        
        # 日期筛选
        if date:
            result = [
                item for item in result
                if self._match_date(item.date, date)
            ]
        
        return result
    
    def _match_date(self, item_date: any, target_date: str) -> bool:
        """匹配日期
        
        Args:
            item_date: 新闻日期（可能是字符串或 datetime.date 对象）
            target_date: 目标日期（YYYY-MM-DD 格式）
        
        Returns:
            是否匹配
        """
        # 转换为字符串
        if isinstance(item_date, str):
            date_str = item_date
        else:
            date_str = str(item_date)
        
        return date_str == target_date or date_str.startswith(target_date)
    
    async def _fetch_cls_news(
        self,
        symbol: str = "全部",
        limit: int = 20
    ) -> NewsResult:
        """获取财联社新闻
        
        Args:
            symbol: "全部" 或 "重点"
            limit: 返回数量
        """
        # AKShare 是同步的，在线程池中执行
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None,
            lambda: ak.stock_info_global_cls(symbol=symbol)
        )
        
        # 限制数量
        if len(df) > limit:
            df = df.head(limit)
        
        # 转换为 NewsItem 列表
        news_items = []
        for _, row in df.iterrows():
            item = NewsItem(
                title=row.get("标题", ""),
                content=row.get("内容", ""),
                date=row.get("发布日期", ""),
                time=row.get("发布时间", ""),
                source="财联社",
            )
            news_items.append(item)
        
        return NewsResult(
            news=news_items,
            total=len(news_items),
            source=f"财联社_{symbol}"
        )
    
    async def _fetch_stock_news(
        self,
        symbol: str,
        limit: int = 20
    ) -> NewsResult:
        """获取个股新闻
        
        Args:
            symbol: 股票代码（如 "000001"）
            limit: 返回数量
        """
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None,
            lambda: ak.stock_news_em(symbol=symbol)
        )
        
        # 限制数量
        if len(df) > limit:
            df = df.head(limit)
        
        # 转换为 NewsItem 列表
        news_items = []
        for _, row in df.iterrows():
            item = NewsItem(
                title=row.get("新闻标题", ""),
                content=row.get("新闻内容", ""),
                date=row.get("发布时间", "")[:10] if row.get("发布时间") else "",
                time=row.get("发布时间", "")[11:19] if row.get("发布时间") else "",
                source=row.get("文章来源", ""),
                url=row.get("新闻链接", ""),
            )
            news_items.append(item)
        
        return NewsResult(
            news=news_items,
            total=len(news_items),
            source=f"东方财富_{symbol}"
        )


# 单例实例
_fetcher = NewsFetcherCls()


async def fetch(
    source: str = "cls_global",
    symbol: Optional[str] = None,
    keyword: Optional[str] = None,
    date: Optional[str] = None,
    limit: int = 20
) -> NewsResult:
    """获取新闻数据的便捷函数
    
    Args:
        source: 新闻源
            - "cls_global": 财联社全球资讯（默认）
            - "cls_important": 财联社重点资讯
            - "stock": 个股新闻（需指定 symbol）
        symbol: 股票代码（仅 source="stock" 时使用）
        keyword: 关键词筛选（在标题和内容中匹配）
        date: 日期筛选（YYYY-MM-DD 格式）
        limit: 返回数量限制
    
    Returns:
        NewsResult: 新闻结果
    
    Examples:
        # 获取财联社全球资讯
        result = await fetch(source="cls_global", limit=10)
        
        # 获取个股新闻
        result = await fetch(source="stock", symbol="000001", limit=5)
        
        # 筛选包含关键词的新闻
        result = await fetch(source="cls_global", keyword="AI", limit=10)
    """
    return await _fetcher.fetch(
        source=source,
        symbol=symbol,
        keyword=keyword,
        date=date,
        limit=limit
    )


def _main():
    """命令行入口"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="获取财经新闻")
    parser.add_argument(
        "--source",
        choices=["cls_global", "cls_important", "stock"],
        default="cls_global",
        help="新闻源"
    )
    parser.add_argument(
        "--symbol",
        help="股票代码（仅 source=stock 时使用）"
    )
    parser.add_argument(
        "--keyword",
        help="关键词筛选"
    )
    parser.add_argument(
        "--date",
        help="日期筛选（YYYY-MM-DD）"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="返回数量限制"
    )
    
    args = parser.parse_args()
    
    # 执行获取
    result = asyncio.run(fetch(
        source=args.source,
        symbol=args.symbol,
        keyword=args.keyword,
        date=args.date,
        limit=args.limit
    ))
    
    # 转换为可序列化的格式
    output = {
        "source": result.source,
        "total": result.total,
        "news": [
            {
                "title": item.title,
                "content": item.content[:200] + "..." if len(item.content) > 200 else item.content,
                "date": str(item.date) if item.date else "",
                "time": str(item.time) if item.time else "",
                "source": item.source,
            }
            for item in result.news
        ]
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _main()
