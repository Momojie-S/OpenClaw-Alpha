# News Fetcher 设计

## 概述

从 skill 目录迁移到 `openclaw_alpha/news/fetcher.py`，作为统一的新闻拉取入口。

Backend 定时任务和 Agent skill 都通过此 fetcher 获取新闻，保证 `news_id` 格式一致。

## 架构

基于 `core.fetcher` 框架，多实现按优先级回退：

```
src/openclaw_alpha/news/fetcher/
├── __init__.py          # export fetch(), NewsItem, NewsResult
├── news_fetcher.py      # 主入口（NewsFetcherCls）
├── akshare_impl.py      # AKShare 实现 + news_id
└── rsshub_impl.py       # RSSHub 实现 + news_id
```

```
NewsFetcher
├── NewsFetcherAkshare (priority=10)  # AKShare 数据源
└── NewsFetcherRsshub  (priority=5)   # RSSHub 数据源
```

## news_id 生成规则

- **RSSHub 源**：`{route_id}_{item.id}`
  - route_id 为路由第一段，如 `cls/telegraph` → `cls`
  - item.id 由 rsshub 模块保底生成（优先 entry.id → entry.guid → link 的 md5）
  - 示例：`cls_abc123`
- **AKShare 源**：无天然唯一 id，需要生成
  - 方案：`{source}_{md5(title+date+time)[:12]}`
  - 示例：`cls_global_a1b2c3d4e5f6`

## 返回结构

```json
{
  "source": "cls",
  "total": 10,
  "news": [
    {
      "news_id": "cls_abc123",
      "title": "标题",
      "content": "内容",
      "date": "2026-04-04",
      "time": "10:00:00",
      "source": "财联社",
      "url": "https://..."
    }
  ]
}
```

核心变化：每条新闻新增 `news_id` 字段。

## 支持的 source

| source | 数据源 | 说明 |
|--------|--------|------|
| `cls_global` | AKShare | 财联社全球资讯 |
| `cls_important` | AKShare | 财联社重点资讯 |
| `stock` | AKShare | 个股新闻（需 symbol） |
| `cls_telegraph` | RSSHub | 财联社电报 |
| `jin10` | RSSHub | 金十快讯 |
| `yicai_brief` | RSSHub | 第一财经简报 |
| `36kr_news` | RSSHub | 36氪资讯 |
| `wallstreetcn_news` | RSSHub | 华尔街见闻 |
| `wallstreetcn_hot` | RSSHub | 华尔街见闻热门 |

## 迁移计划

从 `openclaw_alpha/skills/news_driven_investment/news_fetcher/` 迁移到 `openclaw_alpha/news/fetcher.py`：

1. 主文件 `news_fetcher/` → `news/fetcher/` 目录
2. AKShare 实现独立 `akshare_impl.py`
3. RSSHub 实现独立 `rsshub_impl.py`，增加 news_id 生成
4. `__init__.py` 统一导出

## 调用方式

```python
from openclaw_alpha.news.fetcher import fetch

result = await fetch(source="cls_telegraph", limit=10)
for item in result.news:
    print(item.news_id, item.title)
```

CLI：

```bash
uv run --env-file .env python -m openclaw_alpha.news.cli fetch-news --source cls_telegraph --limit 10
```
