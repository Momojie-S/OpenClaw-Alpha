# News CLI 命令手册

模块入口：`uv run --env-file .env python -m openclaw_alpha.news.cli <command>`

输出统一为 JSON。

---

## fetch-news

拉取新闻，复用 news fetcher 模块。

```bash
uv run --env-file .env python -m openclaw_alpha.news.cli fetch-news \
  [--source cls_global] \
  [--symbol 000001] \
  [--keyword AI] \
  [--date 2026-04-04] \
  [--limit 20]
```

**参数**（与 news fetcher 一致）：
- `--source`：新闻源（默认 `cls_global`）
- `--symbol`：股票代码（仅 `stock` 源使用）
- `--keyword`：关键词筛选
- `--date`：日期筛选（YYYY-MM-DD）
- `--limit`：返回数量（默认 20）

**支持的 source**：
- AKShare：`cls_global`（财联社全球）、`cls_important`（财联社重点）、`stock`（个股新闻，需 --symbol）
- RSSHub：`cls_telegraph`（财联社电报）、`jin10`（金十）、`wallstreetcn_news`（华尔街见闻）等

**返回**：
```json
{"source": "RSSHub_cls_telegraph", "total": 3, "news": [{"news_id": "cls_xxx", "title": "...", ...}]}
```

**news_id 格式**：
- RSSHub：`{route_id}_{item.id}`
- AKShare：`{source}_{md5(title+date+time)[:12]}`

**自动落盘**：返回前自动保存到本地：
- `data/news/{news_id}/news.json`：news_id + title + source + link + published + created_at
- `data/news/{news_id}/content.md`：content 字段
- 已存在的 news_id 跳过（幂等）

---

## update-news

更新新闻字段，按需同步 Milvus。

```bash
uv run --env-file .env python -m openclaw_alpha.news.cli update-news <news_id> \
  [--summary "摘要文本"] \
  [--analysis '{"related_sectors":[...],"related_companies":[...],"worth_deep_analysis":true}'] \
  [--event-id "evt_xxx"]
```

**news_id 对应目录不存在时报错退出。**

**同步逻辑**（多参数同时传入时，先全部写入 news.json，最后统一调用一次 `_sync_to_milvus()`）：
- `--summary`：生成 embedding → 存 embedding.json → 更新 news.json 的 summary 字段
- `--analysis`：更新 news.json 的 analysis 字段，自动从 `related_sectors` + `related_companies[].name` 拼接 entities 字段
- `--event-id`：更新 news.json 的 event_id 字段。不修改 event 文件。

**analysis JSON 结构**（与 news.json.analysis 一致）：
```json
{
  "related_sectors": ["板块1", "板块2"],
  "related_companies": [{"name": "公司名", "listed": true, "code": "000001"}],
  "worth_deep_analysis": false
}
```
- `related_sectors`：必填，数组
- `related_companies`：必填，数组
- `worth_deep_analysis`：必填，布尔

---

## create-event

创建新事件并关联新闻。**事件系统完整设计待后续统一规划，当前仅预留接口。**

---

## search-similar

向量搜索相似新闻。

```bash
uv run --env-file .env python -m openclaw_alpha.news.cli search-similar <news_id> [--top 10]
```

- **news_id 不存在**：返回 `{"error": "news_id xxx not found"}`
- **news_id 无 embedding**：返回 `{"error": "news_id xxx has no embedding yet"}`
- **正常返回**：
```json
{"results": [{"news_id": "...", "event_id": "...", "score": 0.95, "summary": "..."}, ...]}
```

---

## search-keyword

关键词搜索新闻（Milvus BM25 全文检索）。

```bash
uv run --env-file .env python -m openclaw_alpha.news.cli search-keyword <keyword> [--top 10]
```

**实现方式**：Milvus 2.6 原生 BM25。Collection schema 需包含：
- `entities` 字段（VARCHAR）— 作为 BM25 输入
- `bm25_vector` 字段（SPARSE_FLOAT_VECTOR）— 由 `FunctionType.BM25` 自动生成
- 索引：`SPARSE_INVERTED_INDEX`，metric_type `BM25`

查询时传入关键词文本，Milvus 自动分词、匹配、打分。返回 news_id + score，再按 news_id 反查 `data/news/{news_id}/news.json` 获取 summary 和 entities。

**返回**：
```json
{"results": [{"news_id": "...", "summary": "...", "entities": "...", "score": 0.85}, ...]}
```

**news_id 对应目录不存在时跳过该条**。**无结果时返回空列表**：`{"results": []}`

---

## get-news

获取新闻字段。

```bash
uv run --env-file .env python -m openclaw_alpha.news.cli get-news <news_id> [--fields summary,content,analysis]
```

- **news_id 不存在**：返回 `{"error": "news_id xxx not found"}`
- **不指定 --fields**：返回完整 news.json
- **--fields 指定字段**：按 key-value 方式返回指定字段
  ```json
  {"summary": "...", "content": "# 新闻原文..."}
  ```
  - `content`：从 `content.md` 读取
  - 其他字段：从 news.json 读取

---

## get-event

获取事件信息。

```bash
uv run --env-file .env python -m openclaw_alpha.news.cli get-event <event_id>
```

- **event_id 不存在**：返回 `{"error": "event_id xxx not found"}`

---

## 同步时机

所有写操作统一走 `_sync_to_milvus()`，有 embedding 时自动 upsert，无则跳过。
