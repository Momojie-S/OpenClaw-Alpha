# News Fetcher

统一新闻拉取入口，所有调用方（Backend 定时、Agent skill、CLI）通过同一接口获取带 news_id 的新闻。

---

## Purpose

TBD

---

## Requirements

### Requirement: news_id 生成

所有新闻条目必须携带 news_id。

#### Scenario: fetch-news 自动落盘时使用 news_id
- **WHEN** fetch-news 调用 fetcher 获取新闻列表
- **THEN** 每条新闻的 news_id 由 fetcher 生成，用于创建 `data/news/{news_id}/` 目录

#### Scenario: RSSHub 源 news_id
- **WHEN** 通过 RSSHub 源拉取新闻（source 为 cls_telegraph、jin10 等）
- **THEN** 每条新闻的 news_id 格式为 `{route_id}_{item.id}`，route_id 为路由第一段

#### Scenario: AKShare 源 news_id
- **WHEN** 通过 AKShare 源拉取新闻（source 为 cls_global、cls_important、stock）
- **THEN** 每条新闻的 news_id 格式为 `{source}_{md5(title+date+time)[:12]}`

### Requirement: 统一入口

所有新闻拉取通过 `openclaw_alpha/news/fetcher/` 的 `fetch()` 函数。

#### Scenario: Backend 定时任务调用
- **WHEN** Backend 定时任务拉取新闻
- **THEN** 通过 `fetch_and_save()` 调用 `fetch()` 函数获取新闻并自动落盘，使用统一的 news_id 格式

#### Scenario: Agent skill 调用
- **WHEN** Agent 通过 skill 获取新闻
- **THEN** 使用同一个 `fetch()` 函数，news_id 格式与 Backend 一致

#### Scenario: Backend 多源拉取
- **WHEN** Backend 需要拉取多个新闻源（cls_telegraph、jin10 等）
- **THEN** 对每个源调用 `fetch_and_save(source=...)` ，每个源独立返回 saved/skipped 统计

### Requirement: SKILL.md 更新

SKILL.md 需说明 fetcher 的位置和调用方式。

#### Scenario: Agent 读取 SKILL.md
- **WHEN** Agent 查看 news_driven_investment skill 文档
- **THEN** 能找到 fetcher 的正确引用路径和 news_id 说明
