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

## 新闻与事件追踪

我们会在本地记录，新闻和对应事件，用于积累提供更完善的分析。

每条新闻，有唯一标识`news_id`，本地记录保存在 `runtime/data/news/{news_id}/` 目录下。

新闻，有对应的事件，事件唯一标识`event_id`，本地记录保存在 `runtime/data/events/{event_id}/` 目录下。

在分析过程中，应该持续使用CLI工具，进行结构化记录，大部分内容不需要直接编辑对应文件。

以下文件需要额外手动编辑，保存更详细的文本记录:

- `runtime/data/news/{news_id}/report.md`: 记录新闻分析的思路、过程、调研结果、结论等，格式不限。

## 基础分析要求

无论是对新闻做快速分析还是深入分析，都应该遵循以下要求:

1. 对当前新闻进行概括，使用CLI工具写入`summary 新闻概括`，有助于后续搜索相关新闻。
2. 使用CLI工具，在本地搜索相关新闻和事件，回顾历史。
3. 对当前新闻进行分析，使用CLI工具记录，以下内容为必要记录项:
    - analysis，结构化的分析结果
    - event-id，关联已有事件或者新建事件
    - prediction.md，预测内容（markdown）
4. 如果关联到已有事件，读取事件的 `responses/` 目录了解历史市场反应。
5. 分析过程中，应该持续更新 `report.md` 记录

### 分析原则

- **投资视角**：不是新闻摘要，是"这对投资有什么影响"
- **预期差优先**：市场共识外的信息才有超额收益
- **多维度交叉**：新闻 + 板块趋势 + 资金流向，单一维度不可靠

### 快速分析

参考 [任务模板](tasks/quick-news-analysis.md) 用于日常新闻快速筛选和初步评估，输出结构化分析+事件关联+预测建议

### 深入分析

深度分析以**事件**为单位，对快速分析标记为重要的事件进行多维度深入分析。

### 触发机制

详细设计见 [deep-analysis.md](../../docs/design/news/deep-analysis.md)。

简要流程:

1. 快速分析中 `worth_deep_analysis=true` 的新闻关联到事件时，事件 `needs_deep_analysis` 置为 true
2. 快速分析全部完成后，收集所有需要深度分析的事件
3. 判断依据：`len(news_ids) > deep_analysis.analyzed_news_count`
4. 逐事件执行深度分析，基于事件全部新闻（不仅是新增的）
5. 分析完成后 backend 自动更新 `analyzed_news_count` 和 `needs_deep_analysis`

### 分析要求

- 利用其他alpha skill，多角度地对新闻进行深入分析
- 每步分析后，应该考虑该步分析结果是否有其他需考虑的方向，如有，再进行深入分析
- 分析报告存放在 `runtime/data/events/{event_id}/deep_analysis/{date}.md`

多角度分析包括但不限于：板块趋势、资金流向、技术指标、基本面分析、政策影响、历史对比、行业链条、风险因素、关联标的等。

## CLI 工具

用于本地记录、搜索新闻事件，沉淀积累。

**调用方式**：
```bash
cd ~/.openclaw/workspace/skills/OpenClaw-Alpha
uv run python -m openclaw_alpha.news.cli <command> [options]
```

### fetch-news — 拉取新闻并落盘

| Option | 说明 |
|---------|------|
| `--source` | 新闻源（默认 `cls_global`，见下方数据源列表） |
| `--symbol` | 股票代码（仅 `stock` 数据源） |
| `--keyword` | 关键词筛选（匹配标题和内容） |
| `--date` | 日期筛选（YYYY-MM-DD） |
| `--limit` | 返回数量（默认 20） |
| `--data-dir` | 数据根目录（默认 `data/`） |

**数据源列表**：

| Source | 来源 | 类型 | 特点 | 推荐度 |
|--------|------|------|------|:------:|
| `cls_global` | 财联社 | AKShare | 实时、快速、覆盖广 | ⭐⭐⭐ |
| `cls_important` | 财联社 | AKShare | 重点精选，数量少 | ⭐⭐ |
| `stock` | 东方财富 | AKShare | 按股票代码获取个股新闻（需 `--symbol`） | ⭐⭐ |
| `cls_telegraph` | 财联社电报 | RSSHub | 实时快讯，响应快 | ⭐⭐⭐ |
| `jin10` | 金十数据 | RSSHub | 专业金融资讯，更新频繁 | ⭐⭐⭐ |
| `wallstreetcn_hot` | 华尔街见闻热榜 | RSSHub | 最热文章，市场关注度 | ⭐⭐⭐ |
| `wallstreetcn_news` | 华尔街见闻资讯 | RSSHub | 全球市场资讯，专业深度 | ⭐⭐⭐ |
| `yicai_brief` | 第一财经 | RSSHub | 权威财经媒体，覆盖广 | ⭐⭐ |
| `36kr_news` | 36氪 | RSSHub | 科技财经资讯，投资视角 | ⭐⭐ |

**行为**：幂等，已存在的新闻（news_id 目录已创建）自动跳过。

**返回**：`{source, total, saved, skipped, news[]}`
- `news_id`、`news_dir`（数据目录绝对路径）、`title`、`link`、`content`
- `content` 仅在 `saved: true` 时返回

**数据根目录**：默认 `runtime/data/`（通过 `--data-dir` 可指定）

**注意事项**：
- AKShare 接口可能有频率限制
- RSSHub 依赖公共实例，偶尔不稳定，失败时换其他源
- 优先用 AKShare，RSSHub 做补充

### update-news — 更新新闻字段

| Option | 说明 |
|---------|------|
| `news_id` | 新闻 ID（位置参数，必填） |
| `--summary` | 新闻概括（自动生成 embedding 并写入 Milvus） |
| `--analysis` | 结构化分析 JSON（不含 prediction） |
| `--event-id` | 关联事件 ID（双向关联，同时追加到 event.json.news_ids，并置 needs_deep_analysis=true） |
| `--data-dir` | 数据根目录（默认 `data/`） |

**返回**：`{news_id, updated}`

**--analysis JSON 格式**：
```json
{
  "related_sectors": ["板块1", "板块2"],
  "related_companies": [
    {"name": "公司名", "listed": true, "code": "000001"}
  ],
  "worth_deep_analysis": true
}
```

**prediction 保存**：预测内容保存为 markdown 文件 `data/news/{news_id}/prediction.md`。

**行为**：多参数同时传入时，先全部写入 news.json，最后统一 sync Milvus 一次。

---

### search-similar — 向量搜索相似新闻

| Option | 说明 |
|---------|------|
| `news_id` | 源新闻 ID（位置参数，必填） |
| `--top` | 返回数量（默认 10） |
| `--data-dir` | 数据根目录（默认 `data/`） |

**前提**：源新闻必须已通过 `--summary` 生成 embedding。

**返回**：`{results[]}`
- `news_id`、`event_id`、`score`、`summary`

---

### search-keyword — 关键词搜索相似新闻

| Option | 说明 |
|---------|------|
| `keyword` | 搜索关键词（位置参数，必填） |
| `--top` | 返回数量（默认 10） |
| `--data-dir` | 数据根目录（默认 `data/`） |

**返回**：`{results[]}`
- `news_id`、`summary`、`entities`、`score`

---

### get-news — 获取新闻详情

| Option | 说明 |
|---------|------|
| `news_id` | 新闻 ID（位置参数，必填） |
| `--fields` | 指定字段（逗号分隔），始终含 `news_dir` |
| `--data-dir` | 数据根目录（默认 `data/`） |

**返回**：news_id、title、summary、content（通过 `--fields` 时读取）、news_dir 等

---

### get-event — 获取事件信息

| Option | 说明 |
|---------|------|
| `event_id` | 事件 ID（位置参数，必填） |
| `--data-dir` | 数据根目录（默认 `data/`） |

**返回**：event 对象（event_id, title, status, news_ids, created_at, updated_at）

---

---

### create-event — 创建事件并关联首条新闻

| Option | 说明 |
|---------|------|
| `news_id` | 首条关联新闻 ID（位置参数，必填） |
| `--title` | 事件标题（必填） |
| `--data-dir` | 数据根目录（默认 `data/`） |

**行为**：生成 event_id（`evt_{timestamp}_{random4}`），创建 `runtime/data/events/{event_id}/event.json`，同时更新 news.json 的 event_id 字段。幂等。

**返回**：event 对象（event_id, title, status, news_ids, created_at, updated_at）

---

### close-event — 关闭事件

| Option | 说明 |
|---------|------|
| `event_id` | 事件 ID（位置参数，必填） |
| `--data-dir` | 数据根目录（默认 `data/`） |

**行为**：更新 event.json status 为 `closed`。已关闭的事件重复调用会报错。

**返回**：更新后的 event 对象（status=closed）

---

