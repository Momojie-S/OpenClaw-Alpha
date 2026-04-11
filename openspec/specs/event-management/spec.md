# event-management

事件生命周期管理：创建、关闭、列表、查询。

## Purpose

管理 event.json 的 CRUD 操作，事件存储在 `runtime/data/events/{event_id}/event.json`。

## Requirements

### Requirement: Create event
系统 SHALL 提供 `create-event` 命令，创建事件并双向关联首条新闻。

输入：`--title`（必填）、`--news-id`（必填）

#### Scenario: Create new event with first news
- **WHEN** 调用 `create-event --title "xxx" --news-id "news_1"`
- **THEN** 创建 `runtime/data/events/{event_id}/event.json`，包含 title、status="ongoing"、news_ids 含该 news_id、needs_deep_analysis=false、deep_analysis=null
- **AND** 更新 `runtime/data/news/{news_id}/news.json` 的 event_id 字段

#### Scenario: News not found
- **WHEN** 调用 `create-event --news-id "nonexistent"`
- **THEN** 返回错误 `{"error": "news_id xxx not found"}`

### Requirement: Close event
系统 SHALL 提供 `close-event` 命令，将事件状态改为 closed。

#### Scenario: Close ongoing event
- **WHEN** 调用 `close-event evt_xxx`
- **THEN** event.json 的 status 更新为 "closed"，updated_at 更新为当前时间

#### Scenario: Close already closed event
- **WHEN** 调用 `close-event evt_xxx` 且 status 已为 "closed"
- **THEN** 返回错误 `{"error": "event evt_xxx already closed"}`

#### Scenario: Event not found
- **WHEN** 调用 `close-event evt_nonexistent`
- **THEN** 返回错误 `{"error": "event_id xxx not found"}`

### Requirement: List events
系统 SHALL 提供 `list_events()` service 函数，列出事件。不暴露 CLI 命令。

#### Scenario: List all events
- **WHEN** 调用 `list_events()`
- **THEN** 返回所有事件的列表，按 updated_at 降序

#### Scenario: Filter by status
- **WHEN** 调用 `list_events(status="ongoing")`
- **THEN** 只返回 status 为 ongoing 的事件

#### Scenario: Filter needs_deep
- **WHEN** 调用 `list_events(needs_deep=True)`
- **THEN** 只返回 needs_deep_analysis=True 且 status!="closed" 的事件

#### Scenario: Limit results
- **WHEN** 调用 `list_events(limit=10)`
- **THEN** 最多返回 10 条事件

### Requirement: Get event detail
系统 SHALL 提供 `get-event` 命令，返回事件详情。

#### Scenario: Get existing event
- **WHEN** 调用 `get-event evt_xxx`
- **THEN** 返回 event.json 完整内容

#### Scenario: Event not found
- **WHEN** 调用 `get-event evt_nonexistent`
- **THEN** 返回错误 `{"error": "event_id xxx not found"}`
