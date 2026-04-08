---
name: openclaw_alpha_news_driven_investment
description: "新闻驱动投资分析，从新闻中发现投资机会。适用于：(1) 新闻热点追踪，(2) 概念题材挖掘，(3) 动态标的筛选。不适用于：纯技术分析、长期价值投资。"
metadata:
  openclaw:
    emoji: "📰"
    requires:
      bins: ["uv"]
---

# 新闻驱动投资分析

从财经新闻中发现投资机会，关联产业分析和标的筛选。

## CLI 工具

数据源列表见 [references/data-sources.md](references/data-sources.md)。

**调用方式**：
```bash
cd ~/.openclaw/workspace/skills/OpenClaw-Alpha
uv run python -m openclaw_alpha.news.cli <command> [options]
```

| 命令 | Options | 说明 | 返回参数 |
|------|---------|------|----------|
| `fetch-news` | `--source`（默认 cls_global）, `--limit`, `--keyword`, `--date`, `--data-dir` | 拉取新闻并落盘，幂等跳过已存在 | total, saved, skipped, news[] (含 news_id, news_dir, title, link, content) |
| `update-news` | `news_id`, `--summary`, `--analysis`, `--event-id`, `--review`, `--data-dir` | 更新新闻字段；--summary 生成 embedding；--analysis 自动提取 entities；--event-id 双向关联事件；--review 追加到 analysis.reviews[] | 无 |
| `search-similar` | `news_id`, `--top`, `--data-dir` | 向量搜索相似历史新闻（需先有 summary） | results[] (含 news_id, event_id, score, summary) |
| `search-keyword` | `keyword`, `--top`, `--data-dir` | 基于 entities 的 BM25 关键词搜索 | results[] (含 news_id, summary, entities, score) |
| `get-news` | `news_id`, `--fields`, `--data-dir` | 查看新闻详情；始终含 news_dir | news_id, title, summary, content, news_dir 等 |
| `get-event` | `event_id`, `--data-dir` | 查看事件信息 | event_id, title, status, news_ids, created_at 等 |
| `list-events` | `--status`（ongoing/closed）, `--limit`, `--data-dir` | 列出事件，按 updated_at 降序 | events[] |
| `create-event` | `news_id`, `--title`, `--data-dir` | 创建事件并双向关联首条新闻 | event_id, title, news_id |
| `close-event` | `event_id`, `--data-dir` | 关闭事件（更新 status=closed） | 无 |

## 写入闭环

**分析即写入 — 每次分析都应通过 CLI 把结果存下来。**

```
分析一条新闻但不写入  =  一次性分析，无法积累
分析一条新闻并写入    =  对知识库的贡献，后续分析可检索
```

**写入重要**：
- `--summary` → 生成 embedding → Milvus 入库 → search-similar 可命中
- `--analysis` → 提取 entities → BM25 索引 → search-keyword 可找到
- 越多新闻写入，后续分析上下文越丰富

## 使用场景

### 事件追踪

分析时通过 `search-similar` 查找相似新闻 → 按事件分组 → LLM 判断归属已有事件或新建事件 → 写入 prediction → 定期 review 验证预测。设计详见 `docs/design/news/event-tracking.md`。

### 快速分析

系统化评估新闻价值，识别板块和标的。参考 [任务模板](tasks/quick-news-analysis.md) 了解产出要求。

### 手动分析

用户给一条新闻或 URL → 用 `fetch-news` 或 `get-news` 获取数据 → 分析 → `update-news` 写入结果。

### 追踪线索

`search-similar` 或 `search-keyword` 搜索历史 → `get-news` 查看详情 → 结合新信息形成判断。

## 分析原则

- **投资视角**：不是新闻摘要，是"这对投资有什么影响"
- **预期差优先**：市场共识外的信息才有超额收益
- **多维度交叉**：新闻 + 板块趋势 + 资金流向，单一维度不可靠
- **时效敏感**：新闻价值递减，尽快分析
- **风险意识**：新闻驱动多为短期机会，注意追高风险
