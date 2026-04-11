# event-news-linking

新闻与事件的双向关联。

## Purpose

维护 news.json.event_id 和 event.json.news_ids 的双向引用一致性。

## Requirements

### Requirement: Bidirectional event-news linking via create-event
`create-event` SHALL 自动维护双向引用：news.json.event_id + event.json.news_ids。

#### Scenario: Create event sets both sides
- **WHEN** 调用 `create-event --title "xxx" --news-id "news_1"`
- **THEN** event.json.news_ids 包含 news_1，且 news_1 的 news.json.event_id 指向该 event_id

### Requirement: Bidirectional event-news linking via update-news
`update-news --event-id` SHALL 在更新 news.json.event_id 的同时，追加 news_id 到 event.json.news_ids，并置 needs_deep_analysis=true。

#### Scenario: Link news to existing event
- **WHEN** 调用 `update-news news_2 --event-id "evt_xxx"`
- **THEN** news_2 的 news.json.event_id 更新为 "evt_xxx"
- **AND** evt_xxx 的 event.json.news_ids 追加 news_2（含 timestamp）
- **AND** evt_xxx 的 event.json.needs_deep_analysis 置为 true

#### Scenario: Duplicate link is idempotent
- **WHEN** 调用 `update-news news_1 --event-id "evt_xxx"` 且 news_1 已在 event.json.news_ids 中
- **THEN** 不重复追加，不修改 needs_deep_analysis，正常返回

#### Scenario: Event not found
- **WHEN** 调用 `update-news news_1 --event-id "evt_nonexistent"`
- **THEN** 返回错误 `{"error": "event_id xxx not found"}`
