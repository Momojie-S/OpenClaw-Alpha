# News CLI 命令手册

模块入口：`uv run --env-file .env python -m openclaw_alpha.news.cli <command>`

输出统一为 JSON。

---

## fetch-news

拉取新闻（复用 rsshub），返回带 `news_id` 的新闻列表。

```bash
uv run --env-file .env python -m openclaw_alpha.news.cli fetch-news <route>
```

- route: RSSHub 路由，如 `cls/telegraph`
- 返回：`{"items": [{"news_id": "cls_xxx", "title": "...", "link": "...", ...}]}`
- `news_id` 格式：`{route_id}_{item.id}`

---

## update-news

更新新闻字段，按需同步 Milvus。

```bash
uv run --env-file .env python -m openclaw_alpha.news.cli update-news <news_id> \
  [--summary "摘要文本"] \
  [--analysis '{"related_sectors":[...]}'] \
  [--event-id "evt_xxx"]
```

**同步逻辑**：
- `--summary`：生成 embedding → 存 embedding.json → 更新 news.json → upsert Milvus
- `--analysis`：更新 news.json，自动从 related_sectors + related_companies 提取 entities → upsert Milvus（embedding 存在时）
- `--event-id`：更新 news.json + 事件 news_ids → upsert Milvus（embedding 存在时）

## create-event

创建新事件并关联新闻。**事件系统完整设计待后续统一规划，当前仅预留接口。**

```bash
uv run --env-file .env python -m openclaw_alpha.news.cli create-event <news_id> \
  --summary "事件概述"
```

## search-similar

向量搜索相似新闻。

```bash
uv run --env-file .env python -m openclaw_alpha.news.cli search-similar <news_id> [--top 10]
```

输出：
```json
{"results": [{"news_id": "...", "event_id": "...", "score": 0.95, "summary": "..."}, ...]}
```

## search-keyword

关键词搜索新闻（BM25）。

```bash
uv run --env-file .env python -m openclaw_alpha.news.cli search-keyword <keyword> [--top 10]
```

输出：
```json
{"results": [{"news_id": "...", "summary": "...", "entities": "..."}, ...]}
```

## get-news

获取新闻信息。

```bash
uv run --env-file .env python -m openclaw_alpha.news.cli get-news <news_id> [--field summary,content,analysis]
```

- 不指定 `--field`：完整 news.json
- 可传多个字段逗号分隔：`--field summary,content`
- `content` 返回 `{"content": "..."}`
- 其他字段返回对应 JSON

## get-event

获取事件信息。

```bash
uv run --env-file .env python -m openclaw_alpha.news.cli get-event <event_id>
```

---

## 同步时机

所有写操作统一走 `_sync_to_milvus()`，有 embedding 时自动 upsert，无则跳过。
