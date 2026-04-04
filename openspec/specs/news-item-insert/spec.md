# news-item-insert

新闻条目插入，自动建表 + embedding + Milvus 写入。

## Requirements

### Requirement: 新闻条目插入
模块 SHALL 提供 `insert_news()` 函数，接收 news_id、text、entities、可选 event_id，完成 embedding 生成和 Milvus 写入。

#### Scenario: 插入新新闻（collection 已存在）
- **WHEN** 调用 `insert_news("news_1", "标题", "实体", event_id="evt_1")`
- **THEN** 生成 embedding → 写入 Milvus news_items collection

#### Scenario: 插入新新闻（collection 不存在）
- **WHEN** 调用 `insert_news()` 且 news_items collection 不存在
- **THEN** 自动创建 collection（含 schema + index）后插入

### Requirement: Collection Schema
news_items collection SHALL 包含字段：news_id(VARCHAR PK), embedding(FLOAT_VECTOR 1024), event_id(VARCHAR), entities(VARCHAR BM25), created_at(INT64)。

#### Scenario: 自动创建 collection
- **WHEN** ensure_collection() 检测到 news_items 不存在
- **THEN** 创建 collection，embedding 字段使用 AUTOINDEX，entities 字段使用 BM25 全文索引（Jieba 分词）
