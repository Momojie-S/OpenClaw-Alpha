# Deep Analysis Task

## Purpose

Backend 定时任务，扫描需要深度分析的事件并触发 Agent 进行多维度投资分析。

## Requirements

### Requirement: Deep analysis task registration
Backend SHALL register a `deep_analysis` task type with priority 3 in the task registry, alongside existing `news_fetch` (priority 2) and `event_review` (priority 1) tasks.

#### Scenario: Task registered at startup
- **WHEN** backend service starts and quick_news module is enabled
- **THEN** `deep_analysis` task type is registered with priority 3

### Requirement: Deep analysis scanning
The entry function SHALL scan all ongoing events where `needs_deep_analysis == true` and `len(news_ids) > (deep_analysis?.analyzed_news_count ?? 0)`, then trigger Agent analysis for each matched event.

#### Scenario: Events with new pending news
- **WHEN** an ongoing event has `needs_deep_analysis=true` and 3 news_ids but `analyzed_news_count=1`
- **THEN** the event is included in the scan results and triggers deep analysis

#### Scenario: No events need deep analysis
- **WHEN** all ongoing events have `needs_deep_analysis=false` or `analyzed_news_count == len(news_ids)`
- **THEN** scan returns empty list, no Agent sessions are triggered

### Requirement: Deep analysis execution
For each matched event, the system SHALL submit an Agent session with a deep analysis task template, passing event_id and event directory.

#### Scenario: Successful deep analysis
- **WHEN** Agent session completes and writes `deep_analysis/{date}.md` to event directory
- **THEN** system updates event.json: `needs_deep_analysis=false`, `deep_analysis.analyzed_news_count=len(news_ids)`, `deep_analysis.analyzed_at=<current ISO timestamp>`

#### Scenario: Agent session fails
- **WHEN** Agent session fails or times out
- **THEN** system logs the error, does NOT update event.json, task is discarded (no retry)

### Requirement: Deep analysis task template
A task template `deep-news-analysis.md` SHALL be created at `skills/news_driven_investment/tasks/`. The template SHALL instruct the Agent to analyze the event's full context using available skills freely, and write output to `events/{event_id}/deep_analysis/{date}.md`.

#### Scenario: Template provides event context
- **WHEN** Agent receives the task
- **THEN** message includes event_id, event directory path, event title, and list of associated news

### Requirement: Scheduler trigger for deep analysis
APScheduler SHALL trigger `deep_analysis` task enqueue at configurable interval (e.g., every 60 minutes), registered in `register_quick_news_tasks()`.

#### Scenario: Scheduled trigger
- **WHEN** scheduler fires at configured interval
- **THEN** `deep_analysis` task is enqueued (subject to dedup — if already queued, skip)

### Requirement: create-event initializes deep analysis fields
`create-event` CLI SHALL initialize `needs_deep_analysis: false` and `deep_analysis: null` in event.json.

#### Scenario: New event creation
- **WHEN** user runs `create-event --title "xxx"`
- **THEN** event.json contains `"needs_deep_analysis": false, "deep_analysis": null`

### Requirement: update-news sets needs_deep_analysis on event association
`update-news --event-id <id>` SHALL set `needs_deep_analysis: true` on the target event when associating a news item with `worth_deep_analysis=true`.

#### Scenario: News marked as worth deep analysis
- **WHEN** news has `worth_deep_analysis=true` and is associated to an event via `update-news --event-id`
- **THEN** target event's `needs_deep_analysis` is set to `true`

#### Scenario: News not worth deep analysis
- **WHEN** news has `worth_deep_analysis=false` and is associated to an event
- **THEN** target event's `needs_deep_analysis` is NOT changed (may already be true from prior news)
