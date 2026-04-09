# 事件追踪系统设计

## 概述

将离散的新闻串联为可追踪的事件，核心能力：
1. **串联**：自动将相关新闻归入同一事件
2. **预测**：每条新闻分析时生成板块+个股预测
3. **追踪**：定期记录事件的市场反应，形成事件 timeline
4. **总结**：事件关闭时生成最终回顾

```
新闻1 → 预测A（石油↑，航运↓）

事件 timeline:
├─ 2天后 market_response: 石油+3.2%，航运-1.8%，发现铝材+1.5%
└─ 5天后 market_response: 石油回落到+1.5%，航运持续走弱

新闻2 → 预测B（读了事件的 market_responses）

事件 timeline:
└─ 3天后 market_response: 石油-0.3%，航运企稳

事件关闭 → 汇总所有 market_responses
```

## 设计原则

### 新闻是一等公民

- 预测挂在 **news.json** 上
- event.json 只存**不可派生的信息**：标题、状态、新闻引用、市场反应 timeline
- 单独看一条新闻，能看到 prediction

### 追踪由事件驱动

- **新闻分析**：产生 prediction，可以参考事件的 market_responses 做出更好的预测
- **市场反应追踪**：定期记录事件的市场反应，形成 timeline，给以后的分析做参考

### 分析时关联

- 事件关联发生在**分析流程中**，不是独立步骤
- 需要 LLM 理解语义才能判断归属，拉取时无法做到

---

## 数据结构

### news.json — 极简 analysis

```json
{
  "news_id": "wallstreetcn_3769266",
  "title": "特朗普打的越猛，伊朗越强硬：霍尔木兹被推上谈判桌中央！",
  "summary": "...",
  "entities": "石油开采 航运 伊朗 ...",
  "event_id": "evt_1775357774_a3f2",

  "analysis": {
    "related_sectors": ["石油开采", "航运", "军工"],
    "related_companies": [
      {"name": "中国石油", "listed": true, "code": "601857"},
      {"name": "中远海能", "listed": true, "code": "600026"}
    ],
    "worth_deep_analysis": true
  },

  "session": { "...": "..." },
  "created_at": "2026-04-04T12:17:36+08:00",
  "updated_at": "2026-04-08T18:00:00+08:00"
}
```

**analysis 字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `related_sectors` | string[] | ✅ | 相关板块（Milvus entities 用） |
| `related_companies` | object[] | ✅ | 相关公司（Milvus entities 用） |
| `worth_deep_analysis` | boolean | ✅ | 是否值得深度分析 |

### prediction.md — 预测内容

```markdown
# 预测分析

**置信度**：高
**时间窗口**：1-3天

## 板块预测

### 石油开采
- **方向**：上涨
- **理由**：霍尔木兹海峡是石油运输要道，通行威胁直接推升油价

### 航运
- **方向**：下跌
- **理由**：海峡风险增加航运成本和不确定性

## 个股预测

### 中国石油 (601857)
- **方向**：上涨
- **置信度**：中
- **理由**：油价上涨利好上游开采企业

### 中远海能 (600026)
- **方向**：下跌
- **置信度**：中
- **理由**：航运成本上升，利润承压
```

```json
{
  "event_id": "evt_1775357774_a3f2",
  "title": "伊朗威胁封锁霍尔木兹海峡",
  "status": "ongoing",
  "news_ids": [
    {"news_id": "wallstreetcn_3769266", "timestamp": "2026-04-04T12:17:36+08:00"},
    {"news_id": "jin10_xxx", "timestamp": "2026-04-05T18:00:00+08:00"}
  ],
  "created_at": "2026-04-04T12:17:36+08:00",
  "updated_at": "2026-04-10T18:00:00+08:00"
}
```

**市场反应记录**：存储在独立的 markdown 文件中。

```
data/events/{event_id}/
├── event.json              # 元数据
├── summary.md              # 市场反应汇总（timeline + 关键摘要）
└── responses/
    ├── 2026-04-06.md       # 市场反应快照
    ├── 2026-04-10.md       # 市场反应快照
    └── 2026-04-15.md       # 市场反应快照
```

**summary.md 格式**：

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

**responses/{date}.md 格式**：

```markdown
# 市场反应快照：2026-04-06

**关联新闻**：wallstreetcn_3769266

## 板块表现

- **石油开采**：+3.2% 后回落至 +1.5%，盘中一度冲高至 +4.5%
- **航运**：-1.8%，持续走弱

## 新发现

- **铝材**：+1.5%，受石油板块连带影响

## 关键观察

1. 石油板块冲高后快速回落，显示市场对"威胁封锁"的担忧正在消退
2. 航运板块持续承压，可能是对成本上升的担忧
```

**event.json 只存不可从 news.json 派生的信息：**

| 字段 | 说明 | 为什么不能派生 |
|------|------|---------------|
| `event_id` | 唯一标识 | 需要生成 |
| `title` | 事件标题 | LLM 聚合判断，不是单条新闻标题 |
| `status` | ongoing/closed | 事件生命周期状态 |
| `news_ids` | 关联新闻（每项含 news_id 和 timestamp，均为 ISO 8601 字符串） | 串联关系本身 |
| `created_at` | 创建时间（ISO 8601 字符串） | 事件诞生时间 |
| `updated_at` | 最后更新（ISO 8601 字符串） | 最后一条新闻关联时间 |

### 数据关系图

```
                    ┌──────────────────────────┐
                    │       event.json          │
                    │  (极简元数据）            │
                    │  title, status,           │
                    │  news_ids[]              │
                    └──────────┬───────────────┘
                               │
                    event_id 引用（一对多）
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
   │  news.json   │    │  news.json   │    │  news.json   │
   │  新闻1       │    │  新闻2       │    │  新闻3       │
   │              │    │              │    │              │
   │  prediction.md│    │  prediction.md│    │  prediction.md│
   │  (预测内容）  │    │  (预测内容）  │    │  (预测内容）  │
   └──────────────┘    └──────────────┘    └──────────────┘
          │                    │                    │
          └────────────────────┴────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │ responses/          │
                    │  ├ 2026-04-06.md    │
                    │  ├ 2026-04-10.md    │
                    │  └ 2026-04-15.md    │
                    └─────────────────────┘

分析新闻3时，会读到事件的 responses/ 目录，
了解"石油前期+3.2%后回落至+1.5%，航运持续走弱"
```

---

## 流程设计

### 动作一：新闻分析

```
新新闻
  │
  ▼
① update-news --summary
   生成概括 + embedding + Milvus 入库
  │
  ▼
② search-similar top-10
   向量搜索相似历史新闻
  │
  ▼
③ 事件关联
   │
   ├─ 搜索结果按 event_id 分组
   ├─ 取回各候选 event.json
   ├─ LLM 判断：归属已有事件 or 新事件？
   │
   ├─ 新事件 ──▶ create-event + update-news --event-id
   └─ 已有事件 ──▶ update-news --event-id + 更新 event.news_ids
  │
  ▼
④ 读事件历史背景（仅关联到已有事件时）
   │
   ├─ 读事件的 responses/ 目录
   ├─ 了解：之前市场反应了什么，有哪些新发现
   │
   │  这些信息作为新分析的输入（不是输出）
  │
  ▼
⑤ 分析 + 预测
   │
   ├─ 结合历史市场反应做分析
   ├─ responses/ 作为客观事实参考（实际涨跌、新发现的关联标的），不影响独立判断
   └─ 生成 prediction（板块 + 个股）
  │
  ▼
⑥ 写入 prediction.md + update-news --analysis（不含 prediction）
   自动提取 entities + Milvus 同步
  │
  ▼
⑦ 通知
```

### 动作二：定时回顾

```
触发条件:
  - 定时扫描: ongoing 事件下最近 N 天无市场反应记录
  - 手动触发: 用户说 "回顾一下 XXX 事件"

    │
    ▼
① 读事件的 responses/ 目录
   │
    ▼
② 检查是否需要新的市场反应记录（距今超过阈值）
   │
    ▼
③ 查市场数据：当前市场表现
   │
    ▼
④ LLM 分析：与之前的 responses/ 对比，发现新变化
   │
    ▼
⑤ 生成新的市场反应 markdown
   │
    ▼
⑥ 写入 responses/{date}.md
   │
    ▼
⑦ 更新 summary.md（追加新的 timeline 行，更新关键发现）
   │
    ▼
⑧ 通知（可选）：市场反应摘要
```

## 定时回顾实现

### 概述

定时回顾由 Backend 调度，Agent 通过 CLI 写入闭环完成回顾。

```
Backend 调度: 扫描事件 → 筛选新闻 → 触发 Agent Session
Agent 执行:   查市场数据 → 评价预测 → CLI写入
Backend 后续: 读取结果 → 通知
```

核心设计：**追踪即写入**。Agent 在任务中自主决定如何获取市场数据，生成 markdown 文件写入 responses/ 目录，后续分析可参考。

---

### 整体流程

#### Backend 定时流程（纯调度）

```
1. review_all_ongoing_events() 扫描ongoing事件
2. review_event(event_id) 逐个回顾事件
3. 对每个事件：
   - 检查是否需要新的市场反应记录（responses/ 目录下最近文件距今超过阈值）
   - submit_news_review() 触发Agent Session
```

#### Agent 回顾流程

Agent 在任务中自主决定：
- 是否需要查市场数据？
- 查哪些数据（industry_trend、stock_analysis、index_analysis）？
- 如何分析和总结？

最终直接写文件 `data/events/{event_id}/responses/{date}.md`。

#### Backend 后续处理

Agent 完成后 Backend 轮询事件目录：
- 检查 responses/ 目录下是否有新文件
- 读取新文件内容
- 发送回顾通知（可选）

---

### 代码模块

#### Backend（调度）

```
src/openclaw_alpha/backend/quick_news/
├── jobs.py          # 定时任务：review_all_ongoing_events, review_event, submit_news_review
└── task_executor.py # 构造market response任务消息
```

Backend 职责：只管调度和触发，不做market response也不查询市场数据。

#### News 模块（数据操作）

```
src/openclaw_alpha/news/
└── service.py       # 业务逻辑：get_event, list_events, update_news
```

注意：Agent 直接写文件，不需要 CLI 入口。

---

### 任务模板

**路径**：`skills/news_driven_investment/tasks/news-review.md`

任务模板说明回顾目标、输入信息、markdown 格式、要求。Agent 在任务中自主决定如何获取市场数据（调用其他 skill），最终直接写文件 `data/events/{event_id}/responses/{date}.md`。详细内容见文件本身。

---

### 配置

在 `runtime/quick_news/config.yaml` 中新增回顾配置：

```yaml
review:
  enabled: true
  interval_hours: 24              # 回顾间隔
  review_interval_days: 7         # 两次回顾最小间隔
```

---

## 事件关闭实现

### 触发条件

- 后台扫描: status=ongoing 且 7 天无新新闻 → 自动关闭
- 手动触发: 用户说 "XXX事件可以关了" 或 close-event CLI

---

### 流程

```
① 先做一轮回顾（读取 responses/ 目录）
   │
   ▼
② LLM 读取所有 responses/{date}.md → 汇总最终预测准确率
   │
   ▼
③ 更新 event.json status = "closed"
   │
   ▼
④ 通知: "事件 XXX 已关闭，预测准确率 X/Y"
```

---

### 通知格式

```bash
📊 事件关闭：XXX 事件

预测准确率: X/Y (X条准确，Y条预测）

关闭原因: 7天无新新闻 / 手动关闭
```

---

### 事件关联判定

```
输入:
  - 新新闻的 summary
  - search-similar 的 top-10 结果
  - 按 event_id 分组后的各事件信息

LLM Prompt 结构:
  新新闻: {summary}

  候选事件:
  - 事件A: {event.title}
    相关新闻: {新闻1.title} / {新闻2.title}
  - 事件B: {event.title}
    相关新闻: {新闻3.title}

  判断: 这条新闻属于哪个已有事件？还是独立新事件？

输出:
  {"match": "evt_xxx" | null, "reason": "..."}
```

---

## 通知格式

### 新闻分析通知

```
📰 伊朗威胁封锁霍尔木兹海峡（第3条更新）

📌 最新进展: 美伊同意重启谈判

🔮 本次预测:
┌──────────┬──────┬──────────┐
│ 标的     │ 方向 │ 信心度   │
├──────────┼──────┼──────────┤
│ 石油开采 │ ↓    │ 中       │
│ 中国石油 │ ↓    │ 中       │
└──────────┴──────┴──────────┘

📋 历史参考: 石油↑已兑现见顶回落，航运↓准确
```

### 回顾通知

```
🔄 事件回顾: 伊朗威胁封锁霍尔木兹海峡

📊 市场反应快照（4月6日）：

- 石油开采：+3.2% 后回落至 +1.5%
- 航运：-1.8%，持续走弱
- 铝材：+1.5%，受石油板块连带影响

💡 关键观察：石油板块冲高后快速回落，显示市场对"威胁封锁"的担忧正在消退
```

---

## CLI 命令

```bash
# 创建事件（分析流程中 Agent 调用）
uv run python -m openclaw_alpha.news.cli create-event \
  --title "伊朗威胁封锁霍尔木兹海峡" \
  --news-id "wallstreetcn_3769266"

# 关闭事件
uv run python -m openclaw_alpha.news.cli close-event <event_id>

# 列出事件
uv run python -m openclaw_alpha.news.cli list-events \
  [--status ongoing|closed] \
  [--limit 10]

# 获取事件详情
uv run python -m openclaw_alpha.news.cli get-event <event_id>
```

---

## Milvus 变化

无变化。event_id 已在 news_items schema 中，只是现在会被实际填充使用。

通过 event_id 可以：
- 标量过滤：`filter='event_id == "evt_xxx"'` 查某事件的所有新闻
- 去重分组：search-similar 结果按 event_id 聚合

---

## 代码改动清单

### service.py

| 函数 | 说明 |
|------|------|
| `create_event()` | 创建 event.json，关联首条新闻 |
| `update_event_news()` | 追加 news_id 到 event.json |
| `list_events()` | 列出事件，支持 status 过滤 |
| `close_event()` | 更新 status=closed |
| `get_event()` | 获取事件详情 |

### cli.py

| 命令 | 说明 |
|------|------|
| `create-event` | 创建事件 |
| `close-event` | 关闭事件 |
| `list-events` | 列出事件 |
| `get-event` | 获取事件详情 |

### 快速分析任务模板

| 改动 | 说明 |
|------|------|
| 新增步骤 2.5 | 事件关联：search-similar → LLM 判断归属 |
| 新增步骤 3.5 | 读事件历史：responses/ 目录 |
| 扩展 analysis | 只保留结构化字段，prediction 改写文件 |
| 写入 prediction.md | 预测内容保存为 markdown 文件 |

---

---

## 与现有文档的关系

本文档替代 [event-tracking-storage.md](event-tracking-storage.md)。

| 现有文档 | 关系 |
|---------|------|
| [overview.md](overview.md) | 整体架构不变，增加事件追踪层 |
| [news-storage.md](news-storage.md) | news.json 简化 analysis，新增 prediction.md |
| [quick-analysis.md](quick-analysis.md) | 流程增加事件关联和预测步骤 |
| [news-cli.md](news-cli.md) | 新增 create-event/close-event/list-events |
| ~~event-tracking-storage.md~~ | **被本文档替代** |
