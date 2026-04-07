# 事件追踪系统设计

## 概述

将离散的新闻串联为可追踪的事件，核心能力：
1. **串联**：自动将相关新闻归入同一事件
2. **预测**：每条新闻分析时生成板块+个股预测
3. **回顾**：定时回顾已有预测，记录实际表现和后续观察结论
4. **总结**：事件关闭时生成最终回顾

```
新闻1 → 预测A
         ├── 2天后 review: A方向准确，+3.2%
         └── 5天后 review: A见顶回落了，还发现铝材也受影响（漏预测）

新闻2 → 预测B（读了新闻1的 reviews，知道了A的后续表现）
         └── 3天后 review: B方向不对

事件关闭 → 最终回顾通知
```

## 设计原则

### 新闻是一等公民

- 预测、回顾等数据挂在 **news.json** 上
- event.json 只存**不可派生的信息**：标题、状态、新闻引用
- 单独看一条新闻，能看到预测 + 后续的所有验证情况

### 追踪由两种动作驱动

- **新闻分析**：产生 prediction，可以参考已有新闻的 reviews 做出更好的预测
- **定时回顾**：对已有预测追加 reviews，记录实际表现和新发现，给以后的分析做参考

### 分析时关联

- 事件关联发生在**分析流程中**，不是独立步骤
- 需要 LLM 理解语义才能判断归属，拉取时无法做到

---

## 数据结构

### news.json — 扩展 analysis

现有 analysis 字段扩展 `prediction` 和 `reviews`，其余字段不变：

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
    "worth_deep_analysis": true,

    "prediction": {
      "summary": "伊朗强硬表态推高油价预期，航运成本上升",
      "targets": [
        {
          "type": "sector",
          "name": "石油开采",
          "direction": "up",
          "confidence": "high",
          "timeframe": "1-3天",
          "reasoning": "霍尔木兹海峡是石油运输要道，通行威胁直接推升油价"
        },
        {
          "type": "stock",
          "name": "中国石油",
          "code": "601857",
          "direction": "up",
          "confidence": "medium",
          "timeframe": "1-3天",
          "reasoning": "油价上涨利好上游开采企业"
        },
        {
          "type": "sector",
          "name": "航运",
          "direction": "down",
          "confidence": "medium",
          "timeframe": "1-3天",
          "reasoning": "海峡风险增加航运成本和不确定性"
        }
      ]
    },

    "reviews": [
      {
        "reviewed_at": "2026-04-06T18:00:00+08:00",
        "summary": "石油板块+3.2%后开始回落，航运-1.8%持续走弱。铝材受连带影响+1.5%，之前未预测到",
        "target_updates": [
          {
            "name": "石油开采",
            "actual_change": "+3.2%→+1.5%",
            "status": "accurate_then_fading"
          },
          {
            "name": "航运",
            "actual_change": "-1.8%",
            "status": "accurate"
          },
          {
            "name": "铝材",
            "actual_change": "+1.5%",
            "status": "missed"
          }
        ]
      },
      {
        "reviewed_at": "2026-04-08T18:00:00+08:00",
        "summary": "石油已回吐全部涨幅转负，航运企稳",
        "target_updates": [
          {
            "name": "石油开采",
            "actual_change": "-0.3%",
            "status": "inaccurate"
          },
          {
            "name": "航运",
            "actual_change": "-0.2%",
            "status": "accurate"
          }
        ]
      }
    ]
  },

  "session": { "...": "..." },
  "created_at": "2026-04-04T12:17:36+08:00",
  "updated_at": "2026-04-08T18:00:00+08:00"
}
```

#### prediction 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `summary` | string | 预测概述（一两句话） |
| `targets` | array | 预测目标列表（板块+个股） |

#### prediction.target 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `"sector"` \| `"stock"` | 板块或个股 |
| `name` | string | 板块名或公司名 |
| `code` | string | 个股代码（仅 type=stock） |
| `direction` | `"up"` \| `"down"` \| `"neutral"` | 预测影响方向 |
| `confidence` | `"high"` \| `"medium"` \| `"low"` | 信心度 |
| `timeframe` | string | 预期影响时间窗口（如 `"1-3天"`） |
| `reasoning` | string | 简短理由，供后续回顾对照 |

#### reviews 字段说明

| 字段 | 说明 |
|------|------|
| `reviewed_at` | 回顾时间（ISO 8601 字符串，如 `"2026-04-06T18:00:00+08:00"`） |
| `summary` | 对预测表现的总体评价，包括新发现 |
| `target_updates` | 各标的的实际表现 |

reviews 是数组，可以多次追加。每条新闻的 prediction 在事件关闭前可以被多次 review。

#### reviews[].target_updates 字段说明

| 字段 | 说明 |
|------|------|
| `name` | 标的名（板块名或公司名） |
| `actual_change` | 实际涨跌幅 |
| `status` | 预测准确度 |

**status 不限于原始预测的 targets**。review 时可能发现之前没预测到但实际受影响的标的（`status: "missed"`）。

status 取值：
- `"accurate"` — 预测方向与实际一致
- `"inaccurate"` — 预测方向与实际相反
- `"accurate_then_fading"` — 方向对但影响正在消退
- `"missed"` — 之前未预测到但实际受影响
- `"pending"` — 尚未有足够数据判断

### event.json — 纯引用，极简

```json
{
  "event_id": "evt_1775357774_a3f2",
  "title": "伊朗威胁封锁霍尔木兹海峡",
  "status": "ongoing",
  "news_ids": [
    {"news_id": "wallstreetcn_3769266", "timestamp": "2026-04-04T12:17:36+08:00"},
    {"news_id": "jin10_xxx", "timestamp": "2026-04-05T18:00:00+08:00"},
    {"news_id": "cls_xxx", "timestamp": "2026-04-06T18:00:00+08:00"}
  ],
  "created_at": "2026-04-04T12:17:36+08:00",
  "updated_at": "2026-04-06T18:00:00+08:00"
}
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
                    │  (纯引用，极简)            │
                    │  title, entities, status  │
                    │  news_ids[]               │
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
   │  prediction  │    │  prediction  │    │  prediction  │
   │  ├ 石油↑     │    │  ├ 石油↑     │    │  ├ 石油↓     │
   │  └ 航运↓     │    │  └ 航运↓     │    │  └ 航运→     │
   │              │    │              │    │              │
   │  reviews[]   │    │  reviews[]   │    │  reviews[]   │
   │  ├ 2天后:    │    │  ├ 3天后:    │    │  (暂无)      │
   │  │  石油+3.2%│    │  │  石油方向对│    │              │
   │  │  铝材漏了 │    │  │  航运准确  │    │              │
   │  └ 5天后:    │    │              │    │              │
   │     石油回落 │    │              │    │              │
   └──────────────┘    └──────────────┘    └──────────────┘

   分析新闻3时，会读到新闻1、2的 reviews，
   知道"石油前期预测准确但已见顶回落，航运持续准确"
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
   ├─ 读各已有新闻的 prediction + reviews
   ├─ 了解：之前预测了什么，实际表现怎样，发现了什么
   │
   │  这些信息作为新分析的输入（不是输出）
  │
  ▼
⑤ 分析 + 预测
   │
   ├─ 结合历史背景做分析
   ├─ reviews 作为客观事实参考（实际涨跌、新发现的关联标的），不影响独立判断
   └─ 生成 prediction（板块 + 个股）
  │
  ▼
⑥ update-news --analysis（含 prediction）
   自动提取 entities + Milvus 同步
  │
  ▼
⑦ 通知
```

### 动作二：定时回顾

```
触发条件:
  - 定时扫描: ongoing 事件下有 prediction 但最近 N 天无 review 的新闻
  - 手动触发: 用户说 "回顾一下 XXX 事件" 或 review-event CLI

    │
    ▼
① 读事件的 news_ids
   │
    ▼
② 筛选需要 review 的新闻（有 prediction，且上次 review 距今超过阈值）
   │
    ▼
③ 对每条新闻:
   │
   ├─ 读 prediction.targets
   ├─ 查市场数据：各 target 从新闻发布到现在的涨跌幅
   ├─ 检查是否有新的受影响标的（之前未预测但实际受影响的）
   ├─ LLM 评价：准确/不准确/漏掉
   └─ 生成 review
   │
    ▼
④ update-news --review 追加到 news.json 的 reviews[]
   │
    ▼
⑤ 通知（可选）：回顾摘要
```

### 动作三：事件关闭

```
触发条件:
  - 后台扫描: status=ongoing 且 7 天无新新闻 → 自动关闭
  - 手动触发: 用户说 "XXX事件可以关了" 或 close-event CLI

    │
    ▼
① 先做一轮 review（对所有有 prediction 的新闻）
   │
    ▼
② 读所有新闻的最新 reviews → 汇总最终预测准确率
   │
    ▼
③ 更新 event.json status = "closed"
   │
    ▼
④ 通知: "事件 XXX 已关闭，预测准确率 X/Y"
```

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

📊 新闻1 预测回顾:
┌──────────┬──────┬──────────────┬──────────┐
│ 标的     │ 预测 │ 实际         │ 状态     │
├──────────┼──────┼──────────────┼──────────┤
│ 石油开采 │ ↑    │ +3.2%→+1.5% │ ⚠️ 见顶  │
│ 航运     │ ↓    │ -1.8%       │ ✅ 准确  │
│ 铝材     │ -    │ +1.5%       │ 🔍 漏预测 │
└──────────┴──────┴──────────────┴──────────┘

💡 新发现: 铝材受连带影响，后续分析需关注
```

---

## CLI 命令

### 新增命令

```bash
# 创建事件（分析流程中 Agent 调用）
uv run python -m openclaw_alpha.news.cli create-event \
  --title "伊朗威胁封锁霍尔木兹海峡" \
  --news-id "wallstreetcn_3769266"

# 回顾事件预测（定时扫描或手动触发）
uv run python -m openclaw_alpha.news.cli review-event <event_id>

# 关闭事件
uv run python -m openclaw_alpha.news.cli close-event <event_id>

# 列出事件
uv run python -m openclaw_alpha.news.cli list-events \
  [--status ongoing|closed] \
  [--limit 10]
```

### 已有命令扩展

```bash
# update-news --analysis 扩展支持 prediction
uv run python -m openclaw_alpha.news.cli update-news <news_id> \
  --analysis '{"related_sectors": [...], "prediction": {...}}'

# update-news --review 追加回顾（新增）
uv run python -m openclaw_alpha.news.cli update-news <news_id> \
  --review '{"summary": "...", "target_updates": [...]}'

# update-news --event-id 已实现，直接使用
uv run python -m openclaw_alpha.news.cli update-news <news_id> \
  --event-id "evt_xxx"

# get-event 扩展：输出事件信息 + 各新闻的 reviews 汇总
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
| `review_event()` | 对事件下各新闻做 review，追加 reviews[] |
| `close_event()` | 先做 review → 汇总准确率 → 更新 status=closed → 通知 |
| `update_news()` 扩展 | 支持 `--review` 参数追加 review |

### cli.py

| 命令 | 说明 |
|------|------|
| `create-event` | 从占位改为实装 |
| `review-event` | 新增 |
| `close-event` | 新增 |
| `list-events` | 新增 |
| `update-news` 扩展 | 新增 `--review` 参数 |

### 快速分析任务模板

| 改动 | 说明 |
|------|------|
| 新增步骤 2.5 | 事件关联：search-similar → LLM 判断归属 |
| 新增步骤 3.5 | 读事件历史：已有新闻的 prediction + reviews |
| 扩展 analysis | 新增 prediction 字段 |

---

## 市场数据接口

回顾需要查询实际市场表现，依赖已有的 skill：

| 数据需求 | 对应 skill | 说明 |
|---------|-----------|------|
| 板块涨跌幅 | `industry_trend` | 行业板块涨跌排名 |
| 个股涨跌幅 | `stock_analysis` | 个股行情数据 |
| 指数涨跌幅 | `index_analysis` | 大盘指数数据 |

**时间范围**：从新闻 `created_at` 到当前。

---

## 与现有文档的关系

本文档替代 [event-tracking-storage.md](event-tracking-storage.md)。

| 现有文档 | 关系 |
|---------|------|
| [overview.md](overview.md) | 整体架构不变，增加事件追踪层 |
| [news-storage.md](news-storage.md) | news.json 增加 prediction + reviews |
| [quick-analysis.md](quick-analysis.md) | 流程增加事件关联和预测步骤 |
| [news-cli.md](news-cli.md) | 新增 create-event/review-event/close-event/list-events |
| ~~event-tracking-storage.md~~ | **被本文档替代** |
