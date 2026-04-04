# 快速分析设计 v2 — 基于事件跟踪

## 概述

v2 在 v1 基础上引入 Milvus 事件跟踪，核心变化：
1. **Agent 查历史**：通过 CLI 搜索相似新闻，带着上下文分析
2. **Agent 写入库**：分析过程中通过 CLI 写入 Milvus + 本地文件
3. **判断更准**：看到事件发展脉络，而非孤立分析

数据存储与 CLI 命令详见 [news-storage.md](news-storage.md)。

---

## 整体流程

### Backend 定时流程（纯调度）

```
1. RSSHub 拉取新闻，去重
2. 创建本地新闻实体 data/news/{news_id}/news.json + content.md
   - news_id = f"{source}_{item.id}"（source 为路由前缀如 cls、wallstreetcn）
   - 去重：检查 news.json 是否已存在，已存在则跳过
   - 此步骤不操作 Milvus（无 embedding）
3. 拼消息发给 Agent Session
```

### Agent 分析流程

```
1. 概括新闻 → update-news --summary（自动 embedding + Milvus 入库）
2. search-similar 搜索相似新闻，了解历史上下文
   └─ 如有相似 → get-news/get-event 读取详情
3. 分析相关标的、板块、影响
4. update-news --analysis 写入分析结果（自动提取 entities）
5. 事件关联：
   └─ 有相似事件 → update-news --event-id
   └─ 无相似事件 → create-event 新建事件
6. 输出 report.md（可选）+ 判断是否深入
```

---

## 代码模块

### Backend（调度）

```
src/openclaw_alpha/backend/quick_news/
├── jobs.py                 # 定时任务：拉取 + 创建实体 + 触发 Agent
├── rss_fetcher.py          # RSS 拉取（不变）
├── state_manager.py        # 去重状态管理（不变）
├── task_executor.py        # 触发 Agent Session（消息拼接增加 news_id）
├── config.py               # 配置
└── models.py               # 数据模型
```

Backend 职责变简单：只管调度和数据创建，不做分析也不操作 Milvus。

rss_fetcher 复用 rsshub 模块，自动组装 `news_id`（`{route_id}_{item.id}`）并返回。

### News 模块（数据操作 + CLI）

```
src/openclaw_alpha/news/
├── __init__.py
├── fetcher.py              # 通用新闻拉取（复用 rsshub，生成 news_id）
├── store.py                # 底层：ensure_collection(), insert_news()
├── service.py              # 业务逻辑：update_news(), search_similar(), ...
└── cli.py                  # CLI 入口
```

`fetcher.py` 是统一的新闻拉取入口：Backend 定时任务和 Agent skill 都通过它获取新闻，保证 `news_id` 格式一致（`{route_id}_{item.id}`）。

### Core 模块（已有，不变）

```
src/openclaw_alpha/core/
├── milvus/                 # 连接管理
└── embedding/              # 向量生成
```

---

## SKILL.md

在 `skills/news_driven_investment/SKILL.md` 中增加 CLI 工具说明：

- CLI 命令列表和调用方式
- 每个命令的参数和 JSON 输出格式
- 使用场景说明

不暴露内部数据结构，数据通过 CLI 输出自然获取。

Agent 先读 SKILL.md 了解工具能力，再按任务模板步骤执行。深度分析时复用同一套 CLI。

---

## 任务模板变化

v1 任务模板只描述分析流程。v2 增加数据操作步骤：

```
1. 概括新闻 → update-news --summary
2. 搜索历史 → search-similar → get-news/get-event
3. 分析标的、板块、影响
4. update-news --analysis（自动提取 entities）
5. 事件关联 → create-event 或 update-news --event-id
6. 输出 report.md + 判断是否深入
```

---

## Agent 完成后的 Backend 处理

### 1. 更新 news.json

Backend 轮询等待 Agent 完成（超时机制同 v1），完成后：

- 读取 `data/news/{news_id}/news.json`
- 追加 `session` 字段（用于追溯）
- 读取 `worth_deep_analysis` 字段

v2 中 Agent 通过 CLI 直接写入 news.json，不输出 analysis.json。Backend 只追加 session 信息。

### 2. 触发深度分析

读取 `worth_deep_analysis` 字段，决定是否触发深度分析（同 v1）。

v2 中 Backend 不再往 report.md 追加系统信息（已在 news.json session 字段中）。

---

## Agent 输出文件

| 文件 | 定位 | 必需 |
|------|------|------|
| news.json | 元数据 + 分析结果（由 CLI 更新） | ✓ |
| content.md | 新闻原文 | ✓ |
| report.md | 详细分析原因、建议等自由文本 | 可选 |
| progress.md | 分析进度追踪 | 可选 |

---

## 与 v1 的兼容性

| 方面 | v1 | v2 |
|------|----|----|
| RSS 拉取 + 去重 | ✓ | 不变 |
| Backend 触发 | ✓ | 简化（只创建实体+发消息） |
| Agent 分析 | 5 字段 JSON | 3 字段 + 事件上下文 |
| 数据存储 | 无持久化 | Milvus + 本地文件 |
| 事件跟踪 | ✗ | 新增 |
| CLI 工具 | ✗ | 新增 |
| report.md | Agent 可选 + Backend 追加 | Agent 可选，Backend 不追加 |

**迁移**：Backend 逐步改造，Milvus 为空时等同 v1 行为。

---

## 已确认决策

1. **事件关联**：Agent 自主判断，根据搜索结果决定归入已有事件或新建
2. **event.json importance/status**：由 Agent 填写
3. **CLI 输出格式**：JSON
4. **去掉 impact_assessment 和 reason**：分析字段精简为 related_sectors、related_companies、worth_deep_analysis
5. **news.json 不存 content**：原文存 content.md
6. **embedding.json 独立存储**：news.json 不存向量
7. **统一 Milvus 同步入口**：embedding 存在时自动全量 upsert

---

## 相关文档

- [news-fetcher.md](news-fetcher.md) — News Fetcher 设计（迁移 + news_id）
- [news-storage.md](news-storage.md) — 数据结构 + Milvus 同步逻辑
- [news-cli.md](news-cli.md) — CLI 命令手册
- [event-tracking-storage.md](event-tracking-storage.md) — 事件跟踪存储设计
- [quick-analysis.md](quick-analysis.md) — v1 设计（保留参考）
- [overview.md](overview.md) — 新闻分析系统整体设计
