# 事件跟踪系统 — 存储与检索设计

## 目标

跟踪新闻事件的发展脉络，核心能力：
1. **去重/关联**：判断新新闻是否已有事件的后续
2. **搜索**：快速查找相关新闻和事件

## 架构总览

```
新闻输入 → 预处理(摘要/实体/embedding) → Milvus(向量+标量) + 本地文件系统(详情)
```

- **Milvus**：向量检索 + 标量过滤，存最小必要信息
- **本地文件系统**：新闻全文、事件时间线、分析记录

## Milvus Collection 设计

Collection: `news_items`，每条新闻一条记录。

| 字段 | 类型 | 说明 |
|------|------|------|
| news_id | VARCHAR (PK) | 主键，关联本地文件系统 |
| embedding | FLOAT_VECTOR(768) | 摘要的向量（bge-m3） |
| event_id | VARCHAR | 所属事件ID，去重核心字段 |
| entities | VARCHAR (BM25全文索引, Jieba分词) | 实体词空格分隔，如 `"NVDA TSM 芯片 半导体 美股 A股"` |
| created_at | INT64 | 时间戳 |


**为什么是新闻粒度而非事件粒度？**

向量匹配的原子单位是新闻。同一事件的不同阶段（"被调查→回应→处罚"）语义差别大，分开存才能都匹配到。事件通过 `event_id` 聚合。

## 本地文件系统设计

```
data/
├── news/                     # 新闻原始内容
│   └── {news_id}.md          # title, source, url, content, raw_summary
│
├── events/                   # 事件聚合
│   └── {event_id}/
│       ├── meta.json         # summary, entities, importance, status, created_at
│       └── timeline.json     # [{news_id, ts, key_dev}, ...]
│
└── analysis/                 # 分析记录（后续扩展）
    └── {event_id}/
        └── {analysis_id}.md
```

`news_id` 是连接 Milvus 和文件系统的桥梁。

## 去重/关联流程

```
新新闻 → 生成摘要 → embedding
                         │
                         ▼
            Milvus ANN搜索 top-10
                         │
                         ▼
              按 event_id 分组
         ┌────────────────────────┐
         │ event_A: 3条相似新闻    │
         │ event_B: 1条相似新闻    │
         └────────────┬───────────┘
                      │
                      ▼
          取回本地事件 meta.json
                      │
                      ▼
              LLM 判断（带上下文）

  输入: 新新闻摘要 + 各候选事件的summary + 相似新闻标题/摘要
  输出: {"match": "event_A" | null, "reason": "..."}
                      │
                ┌─────┴─────┐
                ▼           ▼
         match=event_A   match=null
                │           │
                ▼           ▼
         归入已有事件     新建事件
```

**LLM 看的是事件+多条新闻，不是单条新闻。** 这样能理解事件完整脉络，避免误判同类不同事。

## event_id 生成

- 入库时即时生成，不做后台聚类
- 新事件：时间戳+随机，如 `evt_1712208000_a3f2`
- 已有事件：沿用 LLM 返回的 event_id

生成后同时写入：
1. Milvus 记录的 `event_id` 字段
2. 本地 `events/{event_id}/timeline.json` 追加记录

## 搜索场景

```
场景: "找跟芯片相关的新闻"

"芯片" → Milvus BM25 全文搜索 entities 字段
       + 按 created_at 排序
       → 返回 [news_id, event_id, ...]
       → 需要详情时，用 news_id 读本地文件
```

## Milvus 模块设计

代码位置：`src/openclaw_alpha/milvus/`

对外接口：
```python
from openclaw_alpha.milvus import get_client

client = get_client()  # 返回 pymilvus.MilvusClient 单例
client.insert(...)
client.search(...)
```

- 模块级 `get_client()` 函数，内部管理单例连接
- 连接参数从环境变量读取（`MILVUS_URI`, `MILVUS_TOKEN`），由 `uv run --env-file` 注入
- 与具体业务无关，通用模块

## 待讨论

- [ ] embedding 模型选择（bge-m3 / 其他）
- [ ] 新闻来源和入库流程
- [ ] 重要性判断标准
