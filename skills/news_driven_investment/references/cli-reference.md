# CLI 参考文档

新闻数据 CLI 工具完整说明。调用方式：

```bash
uv run --env-file .env python -m openclaw_alpha.news.cli <command> [options]
```

下文简写为 `news-cli <command>`。

---

## fetch-news

拉取新闻并自动落盘到本地。

```bash
news-cli fetch-news --source cls_global --limit 20
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--source` | str | `cls_global` | 新闻源 |
| `--limit` | int | 20 | 返回数量 |
| `--keyword` | str | - | 关键词筛选（匹配标题和内容） |
| `--date` | str | - | 日期筛选（YYYY-MM-DD） |
| `--symbol` | str | - | 股票代码（仅 `stock` 源） |
| `--data-dir` | str | `data/` | 数据根目录 |

**行为**：幂等，已存在的新闻（news_id 目录已创建）自动跳过。

**输出**：
```json
{
  "source": "cls_global",
  "total": 20,
  "saved": 15,
  "skipped": 5,
  "news": [
    {
      "news_id": "cls_global_xxx",
      "news_dir": "/absolute/path/to/data/news/cls_global_xxx",
      "title": "新闻标题",
      "link": "https://...",
      "content": "新闻正文",
      "saved": true,
      "skipped": false
    },
    {
      "news_id": "cls_global_yyy",
      "saved": false,
      "skipped": true
    }
  ]
}
```

`news_dir` 是新闻数据目录的绝对路径，用于写入 report.md 等文件。`content` 仅在 `saved: true` 时返回。

数据源列表见 [data-sources.md](data-sources.md)。

---

## update-news

更新新闻字段，支持 summary、analysis、event-id，可组合传入。

```bash
# 写入概括
news-cli update-news <news_id> --summary "一句话概括"

# 写入分析结果
news-cli update-news <news_id> --analysis '{"related_sectors":["银行"],"related_companies":[{"name":"工商银行","listed":true,"code":"601398"}],"worth_deep_analysis":true}'

# 同时写入概括和分析
news-cli update-news <news_id> --summary "概括" --analysis '{...}'
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `news_id` | str | 新闻 ID（位置参数） |
| `--summary` | str | 新闻概括（触发 embedding 生成 + Milvus 入库） |
| `--analysis` | str | JSON 格式分析结果（含 prediction） |
| `--event-id` | str | 关联事件 ID（双向：同时追加 news_id 到 event.json.news_ids） |
| `--review` | str | JSON 格式回顾，追加到 analysis.reviews[] |
| `--data-dir` | str | 数据根目录 |

**analysis JSON 格式**：
```json
{
  "related_sectors": ["板块1", "板块2"],
  "related_companies": [
    {"name": "公司名", "listed": true, "code": "000001"}
  ],
  "worth_deep_analysis": true,
  "prediction": {
    "summary": "预测概述",
    "targets": [
      {
        "type": "sector",
        "name": "石油开采",
        "direction": "up",
        "confidence": "high",
        "timeframe": "1-3天",
        "reasoning": "理由"
      }
    ]
  }
}
```

`prediction` 字段可选，分析时追加。设计详见 `docs/design/news/event-tracking.md`。

**review JSON 格式**：
```json
{
  "summary": "回顾总结：石油+3.2%后回落，航运-1.8%准确",
  "target_updates": [
    {"name": "石油开采", "actual_change": "+3.2%→+1.5%", "status": "accurate_then_fading"},
    {"name": "航运", "actual_change": "-1.8%", "status": "accurate"},
    {"name": "铝材", "actual_change": "+1.5%", "status": "missed"}
  ]
}
```

review 追加到 `analysis.reviews[]` 数组，可多次追加。status 取值：`accurate` / `inaccurate` / `accurate_then_fading` / `missed` / `pending`。

**行为**：多参数同时传入时，先全部写入 news.json，最后统一 sync Milvus 一次。

---

## search-similar

基于 embedding 的向量搜索，查找与指定新闻相似的历史新闻。

```bash
news-cli search-similar <news_id> --top 10
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `news_id` | str | - | 源新闻 ID（必须有 embedding） |
| `--top` | int | 10 | 返回数量 |
| `--data-dir` | str | `data/` | 数据根目录 |

**前提**：源新闻必须已通过 `update-news --summary` 生成 embedding。

**输出**：
```json
{
  "results": [
    {"news_id": "xxx", "event_id": "evt_xxx", "score": 0.85, "summary": "..."},
    {"news_id": "yyy", "event_id": "", "score": 0.72, "summary": "..."}
  ]
}
```

---

## search-keyword

基于 entities 的 BM25 关键词搜索。

```bash
news-cli search-keyword "AI 芯片" --top 10
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `keyword` | str | - | 搜索关键词（位置参数） |
| `--top` | int | 10 | 返回数量 |
| `--data-dir` | str | `data/` | 数据根目录 |

**输出**：
```json
{
  "results": [
    {"news_id": "xxx", "summary": "...", "entities": "NVDA 芯片 半导体", "score": 3.5}
  ]
}
```

---

## get-news

获取单条新闻信息。输出包含 `news_dir`（数据目录绝对路径）。

```bash
# 获取完整信息（含 news_dir）
news-cli get-news <news_id>

# 获取指定字段（始终包含 news_dir）
news-cli get-news <news_id> --fields summary,content,analysis
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `news_id` | str | - | 新闻 ID（位置参数） |
| `--fields` | str | - | 逗号分隔的字段名。`content` 从 content.md 读取 |
| `--data-dir` | str | `data/` | 数据根目录 |

---

## get-event

获取事件聚合信息。

```bash
news-cli get-event <event_id>
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `event_id` | str | 事件 ID（位置参数） |
| `--data-dir` | str | 数据根目录 |

---

## create-event

创建新事件并双向关联首条新闻（news.json.event_id + event.json.news_ids）。

```bash
news-cli create-event <news_id> --title "事件标题"
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `news_id` | str | 首条关联新闻 ID（位置参数） |
| `--title` | str | 事件标题 |
| `--data-dir` | str | 数据根目录（默认 `data/`） |

**行为**：生成 event_id（`evt_{timestamp}_{random4}`），创建 `data/events/{event_id}/event.json`，同时更新 news.json 的 event_id 字段。幂等。

**输出**：
```json
{
  "event_id": "evt_1775357774_a3f2",
  "title": "事件标题",
  "news_id": "wallstreetcn_3769266"
}
```

---

## close-event

关闭事件。

```bash
news-cli close-event <event_id>
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `event_id` | str | 事件 ID（位置参数） |
| `--data-dir` | str | 数据根目录（默认 `data/`） |

**行为**：更新 event.json status 为 `closed`。已关闭的事件重复调用会报错。

---

## list-events

列出事件，按 updated_at 降序。

```bash
# 列出所有事件
news-cli list-events

# 只看进行中的事件
news-cli list-events --status ongoing --limit 10
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--status` | `ongoing` \| `closed` | - | 过滤状态 |
| `--limit` | int | - | 返回数量 |
| `--data-dir` | str | `data/` | 数据根目录 |
