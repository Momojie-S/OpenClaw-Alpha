# 新闻数据存储与更新

## 数据目录

```
data/
├── news/{news_id}/
│   ├── news.json        # 元数据 + 分析结果
│   ├── content.md       # 新闻原文
│   └── embedding.json   # {"vector": [...]} (1024d)
└── events/{event_id}/
    └── event.json       # 事件聚合信息
```

## 数据文件

### news.json

```json
{
  "news_id": "cls_20260404_001",
  "title": "新闻标题",
  "summary": "Agent 概括",
  "entities": "NVDA 芯片 半导体",
  "event_id": "evt_xxx",
  "source": "cls",
  "link": "https://...",
  "published": "2026-04-04T10:00:00+08:00",
  "analysis": {
    "related_sectors": ["板块1"],
    "related_companies": [{"name": "公司", "listed": true, "code": "000001"}],
    "worth_deep_analysis": true
  },
  "session": {
    "job_id": "cron_job_id",
    "session_id": "session_id",
    "context_path": "/path/to/session/context"
  },
  "created_at": 1712208000,
  "updated_at": 1712208000
}
```

### content.md

新闻原文，独立存储避免 news.json 过大。

### embedding.json

```json
{"vector": [0.1, 0.2, ...]}
```

1024 维 float 向量，由 `update-news --summary` 时生成。单独存储保持 news.json 可读。

### event.json

```json
{
  "event_id": "evt_xxx",
  "summary": "事件概述",
  "entities": "NVDA 芯片",
  "importance": "high",
  "status": "ongoing",
  "news_ids": ["news_1", "news_2"],
  "created_at": 1712208000,
  "updated_at": 1712208000
}
```

---

## Milvus 同步

### 统一同步入口

```python
def _sync_to_milvus(news_id: str):
    news = read_news_json(news_id)
    embedding = read_embedding_json(news_id)
    if not embedding:
        return
    client = get_client()
    ensure_collection(client)
    client.upsert("news_items", data=[{
        "news_id": news_id,
        "embedding": embedding["vector"],
        "event_id": news.get("event_id", ""),
        "entities": news.get("entities", ""),
        "created_at": news.get("created_at", 0),
    }])
```

### Milvus Collection Schema（news_items）

| 字段 | 类型 | 说明 |
|------|------|------|
| news_id | VARCHAR (PK) | 新闻唯一标识 |
| embedding | FLOAT_VECTOR(1024) | 语义向量（DashScope text-embedding-v4） |
| bm25_vector | SPARSE_FLOAT_VECTOR | BM25 稀疏向量（自动生成） |
| event_id | VARCHAR | 关联事件 ID |
| entities | VARCHAR | 实体关键词（BM25 输入字段） |
| created_at | INT64 | 创建时间戳 |

**BM25 Function**：`FunctionType.BM25`，输入 `entities` → 输出 `bm25_vector`，Milvus 自动分词生成稀疏向量。

**索引**：
- `embedding`：AUTOINDEX，metric_type `COSINE`
- `bm25_vector`：SPARSE_INVERTED_INDEX，metric_type `BM25`

### 约束

- upsert 必须带 embedding 字段（Milvus 要求非 null 字段全传）
- 统一入口自动从 embedding.json 读取，调用者无需关心
- embedding 不存在时静默跳过

CLI 命令详见 [news-cli.md](news-cli.md)。
