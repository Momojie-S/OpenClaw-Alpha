# -*- coding: utf-8 -*-
"""RSSHub 新闻数据获取实现（复用 rsshub 模块）"""

from typing import Optional
from datetime import datetime

from openclaw_alpha.core.fetcher import FetchMethod
from openclaw_alpha.rsshub import async_fetch_with_fallback
from .models import NewsItem, NewsResult


# RSSHub 路由映射
RSSHUB_ROUTES = {
    "cls_telegraph": "/cls/telegraph",
    "jin10": "/jin10",
    "yicai_brief": "/yicai/brief",
    "36kr_news": "/36kr/news",
    "wallstreetcn_news": "/wallstreetcn/news",
    "wallstreetcn_hot": "/wallstreetcn/hot",
}


class NewsFetcherRsshub(FetchMethod):
    """RSSHub 新闻数据获取实现（复用 rsshub 模块的 fetch_with_fallback）"""

    name = "news_rsshub"
    required_data_source = "http"
    priority = 5

    def is_available(self) -> tuple[bool, None]:
        return (True, None)

    async def fetch(
        self,
        source: str = "cls_telegraph",
        symbol: Optional[str] = None,
        keyword: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 20
    ) -> NewsResult:
        route = RSSHUB_ROUTES.get(source)
        if not route:
            available = ", ".join(RSSHUB_ROUTES.keys())
            raise ValueError(f"参数 source '{source}' 不存在。可用来源：{available}")

        _instance, items = await async_fetch_with_fallback(route)
        route_id = route.strip("/").split("/")[0]
        news_items = self._convert_to_news_items(items, source, route_id)

        # 筛选
        filtered_news = self._filter_news(news_items, keyword=keyword, date=date)
        filtered_news = filtered_news[:limit]

        return NewsResult(
            news=filtered_news,
            total=len(filtered_news),
            source=f"RSSHub_{source}"
        )

    @staticmethod
    def generate_news_id(route_id: str, item_id: str) -> str:
        return f"{route_id}_{item_id}"

    def _convert_to_news_items(self, items, source: str, route_id: str) -> list[NewsItem]:
        source_names = {
            "cls": "财联社",
            "jin10": "金十数据",
            "yicai": "第一财经",
            "36kr": "36氪",
            "wallstreetcn": "华尔街见闻",
        }
        source_name = "RSSHub"
        for key, name in source_names.items():
            if key in source:
                source_name = name
                break

        news_items = []
        for item in items:
            date_str = ""
            time_str = ""
            pub = item.published
            if pub:
                if isinstance(pub, datetime):
                    date_str = pub.strftime("%Y-%m-%d")
                    time_str = pub.strftime("%H:%M:%S")
                elif isinstance(pub, str):
                    try:
                        dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                        date_str = dt.strftime("%Y-%m-%d")
                        time_str = dt.strftime("%H:%M:%S")
                    except (ValueError, TypeError):
                        date_str = pub[:10] if len(pub) >= 10 else ""

            news_items.append(NewsItem(
                news_id=self.generate_news_id(route_id, item.id),
                title=item.title,
                content=item.summary or "",
                date=date_str,
                time=time_str,
                source=source_name,
                url=item.link or "",
            ))

        return news_items

    def _filter_news(
        self,
        news: list[NewsItem],
        keyword: Optional[str] = None,
        date: Optional[str] = None
    ) -> list[NewsItem]:
        result = news
        if keyword:
            keyword_lower = keyword.lower()
            result = [
                item for item in result
                if keyword_lower in item.title.lower()
                or keyword_lower in item.content.lower()
            ]
        if date:
            result = [item for item in result if item.date == date]
        return result
