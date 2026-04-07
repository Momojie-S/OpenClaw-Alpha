# news-review

新闻预测回顾的追加与查询。

## Purpose

支持对 news.json 中 prediction 的后续回顾，记录实际市场表现和新发现的关联标的。

## Requirements

### Requirement: Append review to news
系统 SHALL 通过 `update-news --review` 参数追加 review 到 news.json 的 analysis.reviews[]。

输入：`--review` 接收 JSON 字符串，包含 reviewed_at、summary、target_updates。

#### Scenario: Append first review
- **WHEN** 调用 `update-news news_1 --review '{...}'`，且 news_1 的 reviews 为空
- **THEN** news_1 的 analysis.reviews 包含 1 条 review

#### Scenario: Append additional review
- **WHEN** 调用 `update-news news_1 --review '{...}'`，且 news_1 已有 reviews
- **THEN** 新 review 追加到数组末尾，已有 review 不受影响

#### Scenario: News not found
- **WHEN** 调用 `update-news nonexistent --review '{...}'`
- **THEN** 返回错误 `{"error": "news_id xxx not found"}`

### Requirement: Review data structure
每条 review SHALL 包含：
- `reviewed_at`：ISO 8601 字符串
- `summary`：回顾概述
- `target_updates`：各标的的实际表现列表，每项含 name、actual_change、status
