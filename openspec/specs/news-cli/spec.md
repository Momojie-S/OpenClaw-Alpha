# news-cli

新闻数据 CLI 工具，提供 fetch、update、search、get 等命令行操作。

## Purpose

通过 CLI 管理新闻数据的获取、更新和检索，业务逻辑封装在 service 层供 CLI 和其他模块共用。

## Requirements

### Requirement: service 层封装

所有 CLI 命令的业务逻辑封装在 `news/service.py`，CLI 层只负责参数解析和 JSON 输出。

#### Scenario: CLI 调用 service
- **WHEN** CLI 命令被调用
- **THEN** 解析参数后调用 service 层对应函数，service 返回 dict，CLI 输出 JSON

#### Scenario: service 可被其他模块直接调用
- **WHEN** Backend 或其他模块需要操作新闻数据
- **THEN** 可以直接 import service 层函数，无需走 CLI

#### Scenario: Backend 调用 fetch_and_save 拉取新闻
- **WHEN** Backend 定时任务需要拉取新闻
- **THEN** 直接调用 `fetch_and_save()` 函数，返回 saved/skipped 统计和 news_id 列表

### Requirement: fetch-news 自动落盘

fetch-news 调用 fetcher 后，返回前自动保存到本地。saved 的新闻输出包含完整信息。

#### Scenario: 新新闻自动保存
- **WHEN** fetcher 返回新闻列表
- **THEN** 对每条新闻检查 `data/news/{news_id}/news.json` 是否存在，不存在则创建目录并写入 news.json 和 content.md

#### Scenario: 已有新闻幂等跳过
- **WHEN** news_id 对应的 news.json 已存在
- **THEN** 跳过该条，不覆盖

#### Scenario: saved 新闻输出包含完整信息
- **WHEN** fetch-news 成功保存一条新闻
- **THEN** 输出包含 `news_id`、`news_dir`（绝对路径）、`title`、`link`、`content`（从 content.md 读取）、`saved: true`、`skipped: false`

#### Scenario: skipped 新闻输出精简
- **WHEN** fetch-news 跳过一条已有新闻
- **THEN** 输出仅包含 `news_id`、`saved: false`、`skipped: true`，不包含 news_dir/title/link/content

### Requirement: update-news 统一写入

多参数同时传入时，先全部写入 news.json，最后统一 sync 一次。

#### Scenario: 只传 summary
- **WHEN** update-news 传入 `--summary`
- **THEN** 生成 embedding → 存 embedding.json → 更新 news.json summary 字段 → sync Milvus

#### Scenario: 只传 analysis
- **WHEN** update-news 传入 `--analysis`
- **THEN** 解析 JSON（字段为 related_sectors、related_companies、worth_deep_analysis） → 更新 news.json analysis 字段 → 拼接 entities → sync Milvus（有 embedding 时）

#### Scenario: 同时传 summary + analysis
- **WHEN** update-news 同时传入 `--summary` 和 `--analysis`
- **THEN** 先生成 embedding → 更新 summary → 更新 analysis + entities → 统一 sync 一次

#### Scenario: news_id 不存在
- **WHEN** update-news 传入的 news_id 目录不存在
- **THEN** 返回 `{"error": "news_id xxx not found"}`

### Requirement: search-similar 向量搜索

基于 news_id 的 embedding 搜索相似新闻。

#### Scenario: 正常搜索
- **WHEN** search-similar 传入有 embedding 的 news_id
- **THEN** 用其 embedding 在 Milvus 做向量搜索，返回 news_id + score + summary（从 news.json 反查）

#### Scenario: news_id 不存在
- **WHEN** search-similar 传入的 news_id 目录不存在
- **THEN** 返回 `{"error": "news_id xxx not found"}`

#### Scenario: 无 embedding
- **WHEN** search-similar 传入的 news_id 没有 embedding.json
- **THEN** 返回 `{"error": "news_id xxx has no embedding yet"}`

### Requirement: search-keyword BM25 搜索

基于关键词的全文检索。

#### Scenario: 正常搜索
- **WHEN** search-keyword 传入关键词
- **THEN** 用 Milvus BM25 搜索 entities 字段，返回 news_id + score + summary + entities（从 news.json 反查）

#### Scenario: 无结果
- **WHEN** 搜索无匹配
- **THEN** 返回 `{"results": []}`

### Requirement: get-news 按字段查询

#### Scenario: 不指定 fields
- **WHEN** get-news 不传 `--fields`
- **THEN** 返回完整 news.json + `news_dir`（绝对路径）

#### Scenario: 指定 fields
- **WHEN** get-news 传入 `--fields summary,content`
- **THEN** 按 key-value 返回指定字段（含 `news_dir`），content 从 content.md 读取

#### Scenario: news_id 不存在
- **WHEN** get-news 传入的 news_id 目录不存在
- **THEN** 返回 `{"error": "news_id xxx not found"}`

### Requirement: get-event 查询

#### Scenario: event_id 不存在
- **WHEN** get-event 传入的 event_id 目录不存在
- **THEN** 返回 `{"error": "event_id xxx not found"}`

### Requirement: analysis_status 状态管理

news.json 中通过 `analysis_status` 字段追踪分析进度，由 Backend 负责写入和更新，Agent 不碰此字段。

#### Scenario: 新闻刚落盘时无 analysis_status
- **WHEN** fetch_and_save 创建新的 news.json
- **THEN** news.json 不包含 analysis_status 字段

#### Scenario: Backend 触发分析时写入 pending
- **WHEN** Backend 决定对某条新闻触发 Agent 分析
- **THEN** 更新 news.json，写入 `analysis_status: "pending"`

#### Scenario: Agent 分析成功后 Backend 写入 done
- **WHEN** Backend 确认 Agent 成功完成分析
- **THEN** 更新 news.json，写入 `analysis_status: "done"`，并从 analysis 中提取 worth_deep_analysis

#### Scenario: Agent 分析失败后 Backend 写入 failed
- **WHEN** Agent 分析超时或出错
- **THEN** 更新 news.json，写入 `analysis_status: "failed"`

#### Scenario: 待分析新闻筛选
- **WHEN** Backend 需要找出待分析的新闻
- **THEN** 扫描 data/news/ 下所有 news.json，筛选 analysis_status 为空或 "failed" 的新闻

### Requirement: Backend 直接 import service 层

Backend 通过 import 调用 news/service.py 的函数，不走 subprocess CLI。

#### Scenario: Backend import fetch_and_save
- **WHEN** Backend jobs.py 执行定时拉取
- **THEN** 调用 `from openclaw_alpha.news.service import fetch_and_save`，直接调用函数

#### Scenario: Backend import update_news 写状态
- **WHEN** Backend 需要写入 analysis_status
- **THEN** 调用 `update_news(news_id, ...)` 或直接操作 news.json（通过已有的 read_news_json / write_news_json）

### Requirement: 错误统一格式

所有错误以 `{"error": "message"}` 格式返回，CLI 以 exit code 1 退出。
