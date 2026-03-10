# -*- coding: utf-8 -*-
"""RSSHub 新闻数据获取实现

从 RSSHub 公共实例获取新闻数据，支持 JSON 格式输出。
"""

import asyncio
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field

import httpx

from openclaw_alpha.core.fetcher import FetchMethod


# 复用 NewsItem 和 NewsResult 定义（避免循环导入）
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


# RSSHub 路由映射
RSSHUB_ROUTES = {
    "cls_telegraph": "/cls/telegraph",  # 财联社电报
    "xueqiu_today": "/xueqiu/today",    # 雪球今日话题
}

# 默认 RSSHub 实例（按优先级）
DEFAULT_RSSHUB_INSTANCES = [
    "rsshub.liumingye.cn",  # 香港节点，国内访问友好
    "rsshub.ktachibana.party",  # 美国节点
]


class NewsFetcherRsshub(FetchMethod):
    """RSSHub 新闻数据获取实现"""
    
    name = "news_rsshub"
    required_data_source = "http"  # HTTP 客户端，不需要特定数据源
    priority = 5  # 低于 AKShare（优先级 10）
    
    def is_available(self) -> tuple[bool, None]:
        """RSSHub 总是可用（只需要 HTTP 客户端）"""
        return (True, None)
    
    def __init__(self, rsshub_instance: Optional[str] = None):
        """初始化 RSSHub Fetcher
        
        Args:
            rsshub_instance: RSSHub 实例地址（不含 https://），默认使用推荐实例
        """
        super().__init__()
        self.rsshub_instance = rsshub_instance or DEFAULT_RSSHUB_INSTANCES[0]
    
    async def fetch(
        self,
        source: str = "cls_telegraph",
        symbol: Optional[str] = None,
        keyword: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 20
    ) -> NewsResult:
        """从 RSSHub 获取新闻并筛选
        
        Args:
            source: RSSHub 路由名称
                - "cls_telegraph": 财联社电报（默认）
                - "xueqiu_today": 雪球今日话题
            keyword: 关键词筛选（在标题和内容中匹配）
            date: 日期筛选（YYYY-MM-DD 格式）
            limit: 返回数量限制
        
        Returns:
            NewsResult: 新闻结果
        """
        # 获取路由路径
        route = RSSHUB_ROUTES.get(source)
        if not route:
            available = ", ".join(RSSHUB_ROUTES.keys())
            raise ValueError(
                f"参数 source '{source}' 不存在（收到 '{source}'）。"
                f"可用来源：{available}"
            )
        
        # 获取 RSSHub 数据
        raw_news = await self._fetch_from_rsshub(route, limit * 5)
        
        # 转换为 NewsItem
        news_items = self._convert_to_news_items(raw_news, source)
        
        # 应用筛选
        filtered_news = self._filter_news(news_items, keyword=keyword, date=date)
        
        # 限制数量
        filtered_news = filtered_news[:limit]
        
        return NewsResult(
            news=filtered_news,
            total=len(filtered_news),
            source=f"RSSHub_{source}"
        )
    
    async def _fetch_from_rsshub(self, route: str, limit: int) -> list[dict]:
        """从 RSSHub 获取 JSON 数据
        
        Args:
            route: RSSHub 路由路径（如 /cls/telegraph）
            limit: 获取数量
        
        Returns:
            新闻列表（JSON 格式）
        """
        url = f"https://{self.rsshub_instance}{route}?format=json"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                # RSSHub JSON 返回格式：{"items": [...]}
                items = data.get("items", [])
                return items[:limit]
                
            except httpx.HTTPStatusError as e:
                raise RuntimeError(
                    f"连接 RSSHub API 失败（HTTP {e.response.status_code}）。"
                    f"请检查网络连接或尝试其他 RSSHub 实例。"
                ) from e
            except httpx.RequestError as e:
                raise RuntimeError(
                    f"连接 RSSHub API 超时。请检查网络连接后重试。"
                ) from e
    
    def _convert_to_news_items(self, raw_news: list[dict], source: str) -> list[NewsItem]:
        """将 RSSHub JSON 转换为 NewsItem
        
        Args:
            raw_news: RSSHub 返回的新闻列表
            source: 来源标识
        
        Returns:
            NewsItem 列表
        """
        news_items = []
        
        for item in raw_news:
            # 解析时间
            date_str = ""
            time_str = ""
            date_published = item.get("date_published", "")
            if date_published:
                try:
                    dt = datetime.fromisoformat(date_published.replace("Z", "+00:00"))
                    date_str = dt.strftime("%Y-%m-%d")
                    time_str = dt.strftime("%H:%M:%S")
                except (ValueError, TypeError):
                    date_str = date_published[:10] if len(date_published) >= 10 else ""
            
            # 来源名称
            source_name = "财联社" if "cls" in source else "雪球" if "xueqiu" in source else "RSSHub"
            
            # 创建 NewsItem
            news_item = NewsItem(
                title=item.get("title", ""),
                content=item.get("summary", "") or item.get("content_html", ""),
                date=date_str,
                time=time_str,
                source=source_name,
                url=item.get("url", "") or item.get("id", ""),
            )
            news_items.append(news_item)
        
        return news_items
    
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
                if item.date == date
            ]
        
        return result
