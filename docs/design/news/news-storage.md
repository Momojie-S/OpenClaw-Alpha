# 新闻数据存储与更新

## 数据目录

```
data/
├── news/{news_id}/
│   ├── news.json        # 元数据 + 分析结果（结构化）
│   ├── content.md       # 新闻原文
│   ├── prediction.md    # 预测内容（markdown）
│   └── summary_vector.json   # {"vector": [...]} (1024d)
└── events/{event_id}/
    ├── event.json       # 事件聚合信息
    ├── summary.md       # 市场反应汇总
    └── responses/       # 市场反应快照
        ├── 2026-04-06.md
        └── 2026-04-10.md
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

**analysis 字段**：仅保留结构化字段供 Milvus 使用，预测内容放在 `prediction.md`。

### prediction.md

预测内容，markdown 格式：

```markdown
# 预测分析

**置信度**：高
**时间窗口**：1-3天

## 板块预测

### 石油开采
- **方向**：上涨
- **理由**：霍尔木兹海峡是石油运输要道

### 航运
- **方向**：下跌
- **理由**：海峡风险增加航运成本

## 个股预测

### 中国石油 (601857)
- **方向**：上涨
- **理由**：油价上涨利好上游开采企业
```

### content.md

新闻原文，独立存储避免 news.json 过大。

### summary_vector.json

```json
{"vector": [0.1, 0.2, ...]}
```

1024 维 float 向量，由 `update-news --summary` 时生成（DashScope text-embedding-v4）。单独存储保持 news.json 可读。

### event.json

```json
{
  "event_id": "evt_xxx",
  "title": "事件标题",
  "status": "ongoing",
  "news_ids": [
    {"news_id": "news_1", "timestamp": "2026-04-04T12:00:00+08:00"},
    {"news_id": "news_2", "timestamp": "2026-04-05T18:00:00+08:00"}
  ],
  "created_at": 1712208000,
  "updated_at": 1712208000
}
```

### summary.md

市场反应汇总，提供事件 timeline 和关键发现：

```markdown
# 事件：伊朗威胁封锁霍尔木兹海峡

**状态**：ongoing
**创建时间**：2026-04-04
**相关新闻**：3 条

## 市场反应 Timeline

| 日期 | 关键表现 | 备注 |
|------|---------|------|
| 4月6日 | 石油+3.2%→+1.5%，航运-1.8% | 铝材异动+1.5% |
| 4月10日 | 石油-0.3%，航运企稳 | 已回吐全部涨幅 |
| 4月15日 | 石油-0.5%，航运+0.3% | 美伊同意重启谈判 |

## 关键发现

1. **石油板块**：初期+3.2%后快速回落，市场对"威胁"因素消化迅速
2. **航运板块**：持续承压后企稳，可能已见底
3. **铝材**：意外的连带影响，通胀传导效应

## 预测追踪

- **石油开采**：预测↑，实际先+后-（初期准确，后期不准确）
- **航运**：预测↓，实际持续走弱后企稳（准确）

---

*最后更新：2026-04-15* 
*完整快照详见 responses/ 目录*
```

### responses/{date}.md

市场反应快照，markdown 格式：

```markdown
# 市场反应快照：2026-04-06

**关联新闻**：news_1

## 板块表现

- **石油开采**：+3.2% 后回落至 +1.5%
- **航运**：-1.8%，持续走弱

## 新发现

- **铝材**：+1.5%，受石油板块连带影响

## 关键观察

1. 石油板块冲高后快速回落
2. 航运板块持续承压
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
        "summary_vector": embedding["vector"],
        "event_id": news.get("event_id", ""),
        "entities": news.get("entities", ""),
        "created_at": news.get("created_at", 0),
    }])
```

### Milvus Collection Schema（news_items）

| 字段 | 类型 | 说明 |
|------|------|------|
| news_id | VARCHAR(256) (PK) | 新闻唯一标识 |
| summary_vector | FLOAT_VECTOR(1024) | 语义向量（从 summary 生成，DashScope text-embedding-v4） |
| entities_vector | SPARSE_FLOAT_VECTOR | 关键词向量（从 entities 自动生成，勿手动写入） |
| event_id | VARCHAR(256) | 关联事件 ID |
| entities | VARCHAR(2048) | 实体关键词，空格分隔（如 `"石油化工 黄金 中国石油"`） |
| created_at | INT64 | 创建时间戳 |

**BM25 Function**：`FunctionType.BM25`，输入 `entities` → 输出 `entities_vector`，Milvus 自动分词生成稀疏向量。

**entities 字段 Analyzer**：使用 `chinese` 内置分词器。

> **为什么不选其他 analyzer：**
> - `jieba`：Zilliz Cloud Serverless 不支持（仅自建 Milvus 可用）
> - `standard`：按空格切 token，`"中国石油"` 作为完整 token，搜 `"石油"` 无法命中
> - `chinese`：中文分词，`"中国石油"` → `["中国", "石油"]`，支持子串搜索

**索引**（两个向量字段，搜索时必须指定 `anns_field`）：
- `summary_vector`：AUTOINDEX，COSINE — 用于 `search-similar`（语义匹配）
- `entities_vector`：SPARSE_INVERTED_INDEX，BM25 — 用于 `search-keyword`（关键词搜索）

### 连接注意事项

Zilliz Cloud Serverless 的 URI 必须显式带 `:443` 端口：

```
MILVUS_URI=https://xxx.serverless.gcp-us-west1.cloud.zilliz.com:443
```

pymilvus 默认用 19530 端口（自建 Milvus 默认），Zilliz Cloud Serverless 不开放 19530，不带端口会导致连接超时。

### 约束

- upsert 必须带 summary_vector 字段（Milvus 要求非 null 字段全传）
- 统一入口自动从 summary_vector.json 读取，调用者无需关心
- summary_vector 不存在时静默跳过
- entities 在 sync 时自动做 list→string 转换（news.json 可能为 list）

CLI 命令详见 [news-cli.md](news-cli.md)。
