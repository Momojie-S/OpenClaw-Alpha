---
name: openclaw_alpha_news_monitor
description: "财经新闻监控，获取实时财经新闻并支持筛选。适用于：(1) 查看今日热点新闻，(2) 按关键词筛选新闻，(3) 追踪个股相关新闻。不适用于：新闻情感分析、历史新闻归档、研报获取。"
metadata:
  openclaw:
    emoji: "📰"
    requires:
      bins: ["uv"]
---

# 财经新闻监控

快速获取今日财经新闻，支持关键词和日期筛选。

## 使用说明

### 获取今日热点（默认）

```bash
# 不传参数，自动返回今日热点 Top 10
uv run --env-file .env python skills/news_driven_investment/scripts/news_fetcher/news_fetcher.py --limit 10
```

### 按关键词筛选

```bash
# 筛选包含 "AI" 的新闻
uv run --env-file .env python skills/news_driven_investment/scripts/news_fetcher/news_fetcher.py --keyword "AI" --limit 10

# 筛选包含 "新能源" 的新闻
uv run --env-file .env python skills/news_driven_investment/scripts/news_fetcher/news_fetcher.py --keyword "新能源" --limit 10
```

### 按股票筛选

```bash
# 获取个股相关新闻
uv run --env-file .env python skills/news_driven_investment/scripts/news_fetcher/news_fetcher.py --source stock --symbol 000001 --limit 10
```

### 按日期筛选

```bash
# 获取指定日期的新闻
uv run --env-file .env python skills/news_driven_investment/scripts/news_fetcher/news_fetcher.py --date "2026-03-07" --limit 10
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--source` | 新闻源：`cls_global`（默认）、`cls_important`、`stock` | cls_global |
| `--keyword` | 关键词筛选 | 无 |
| `--symbol` | 股票代码（仅 source=stock 时使用） | 无 |
| `--date` | 日期筛选（YYYY-MM-DD） | 今天 |
| `--limit` | 返回数量 | 20 |

## 输出格式

每条新闻包含：

| 字段 | 说明 |
|------|------|
| title | 新闻标题 |
| source | 新闻来源 |
| date | 发布日期 |
| time | 发布时间 |
| content | 内容摘要 |

## 使用场景

### 场景 1：懒人查看今日热点

```
使用者：最近有什么财经新闻？
Agent：运行 news_fetcher，返回 Top 10 热点新闻
```

### 场景 2：关注特定话题

```
使用者：AI 相关的新闻有哪些？
Agent：运行 news_fetcher --keyword "AI"，返回相关新闻
```

### 场景 3：追踪个股动态

```
使用者：平安银行最近有什么新闻？
Agent：运行 news_fetcher --source stock --symbol 000001
```

## 与其他 Skill 联动

| Skill | 联动方式 |
|-------|---------|
| market_sentiment | 新闻热度作为情绪判断依据 |
| risk_alert | 负面新闻作为风险信号 |
| industry_trend | 行业新闻热度作为板块热度参考 |
| stock_analysis | 个股新闻作为分析补充 |

## 注意事项

1. **时效性**：新闻价值随时间递减，建议及时分析
2. **关键词精确性**：关键词会同时匹配标题和内容
3. **数据源限制**：AKShare 接口可能有频率限制，不要频繁调用
