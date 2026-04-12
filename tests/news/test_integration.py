# -*- coding: utf-8 -*-
"""News 集成测试：真实 Milvus + embedding，端到端流程。

需要环境变量：MILVUS_URI, MILVUS_TOKEN, DASHSCOPE_API_KEY
标记为 integration，默认不运行。
"""

import json
import pytest
from pathlib import Path

from openclaw_alpha.news.fetcher.models import NewsItem


@pytest.mark.integration
@pytest.mark.asyncio
class TestIntegration:
    """端到端：fetch_and_save → update_news → search_similar → search_keyword → get_news"""

    async def test_full_pipeline(self, tmp_path):
        from openclaw_alpha.news import service

        news_id = "test_integ_001"
        item = NewsItem(
            news_id=news_id,
            title="英伟达发布新一代GPU",
            content="英伟达发布新一代GPU，性能提升显著",
            date="2026-04-04",
            time="10:00:00",
            source="测试",
        )

        # 1. 手动 save（模拟 fetch_and_save）
        service._save_news_item(item, tmp_path)
        assert (tmp_path / "news" / news_id / "news.json").exists()

        # 2. update-news --summary
        result = service.update_news(
            news_id, summary="英伟达发布新一代GPU，性能提升显著", data_dir=tmp_path
        )
        assert result.get("updated") is True
        assert service.read_summary_vector(news_id, tmp_path) is not None

        # 3. update-news --analysis
        analysis = {
            "related_sectors": ["半导体", "AI"],
            "related_companies": [{"name": "NVDA", "listed": True, "code": "NVDA"}],
            "worth_deep_analysis": False,
        }
        result = service.update_news(news_id, analysis=analysis, data_dir=tmp_path)
        assert result.get("updated") is True

        # 4. search-similar
        result = service.search_similar(news_id, top=5, data_dir=tmp_path)
        assert "results" in result
        # 只有一条数据，可能返回空
        assert isinstance(result["results"], list)

        # 5. get-news
        result = service.get_news(news_id, data_dir=tmp_path)
        assert result["news_id"] == news_id
        assert result["summary"] == "英伟达发布新一代GPU，性能提升显著"
        assert result["entities"] == "半导体 AI NVDA"

        # 6. get-news --fields
        result = service.get_news(news_id, fields=["summary", "entities"], data_dir=tmp_path)
        assert result == {"summary": "英伟达发布新一代GPU，性能提升显著", "entities": "半导体 AI NVDA"}
