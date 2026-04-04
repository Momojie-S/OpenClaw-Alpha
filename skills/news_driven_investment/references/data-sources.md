# 数据源参考

## 命令格式

```bash
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source <SOURCE> [--limit N] [--keyword "关键词"] [--date "YYYY-MM-DD"] [--symbol 000001]
```

## AKShare 数据源（优先使用）

| Source | 来源 | 特点 | 推荐度 |
|--------|------|------|:------:|
| `cls_global` | 财联社 | 实时、快速、覆盖广 | ⭐⭐⭐ |
| `cls_important` | 财联社 | 重点精选，数量少 | ⭐⭐ |
| `stock` | 东方财富 | 按股票代码获取个股新闻（需 `--symbol`） | ⭐⭐ |

## RSSHub 数据源（备选）

| Source | 来源 | 特点 | 推荐度 |
|--------|------|------|:------:|
| `cls_telegraph` | 财联社电报 | 实时快讯，响应快 | ⭐⭐⭐ |
| `jin10` | 金十数据 | 专业金融资讯，更新频繁 | ⭐⭐⭐ |
| `wallstreetcn_hot` | 华尔街见闻热榜 | 最热文章，市场关注度 | ⭐⭐⭐ |
| `wallstreetcn_news` | 华尔街见闻资讯 | 全球市场资讯，专业深度 | ⭐⭐⭐ |
| `yicai_brief` | 第一财经 | 权威财经媒体，覆盖广 | ⭐⭐ |
| `36kr_news` | 36氪 | 科技财经资讯，投资视角 | ⭐⭐ |

## 筛选参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--keyword` | 关键词筛选（标题和内容匹配） | `--keyword "AI"` |
| `--date` | 日期筛选（YYYY-MM-DD） | `--date "2026-03-07"` |
| `--limit` | 返回数量限制（默认 20） | `--limit 10` |
| `--symbol` | 股票代码（仅 `stock` 源） | `--symbol 000001` |

## 使用示例

```bash
# 财联社全球资讯（默认，最常用）
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source cls_global --limit 20

# 按关键词筛选
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source cls_global --keyword "AI" --limit 10

# 个股新闻
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source stock --symbol 000001 --limit 5

# 华尔街见闻热榜
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source wallstreetcn_hot --limit 10
```

## 注意事项

- AKShare 接口可能有频率限制，不要短时间内重复调用
- RSSHub 依赖公共实例，偶尔不稳定，失败时换其他源
- 优先用 AKShare，RSSHub 做补充
