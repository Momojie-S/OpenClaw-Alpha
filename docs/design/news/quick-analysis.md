# 快速分析设计

## 概述

快速分析是新闻分析系统的第一层，由 Backend 定时触发，Agent 通过 CLI 写入闭环完成分析。

```
Backend 调度: 拉取新闻 → 创建实体 → 触发 Agent Session
Agent 执行:   概括→搜索历史→分析→CLI写入→判断深入
Backend 后续: 读取结果 → 通知 → 触发深度分析（可选）
```

核心设计：**分析即写入**。Agent 通过 CLI 操作数据（update-news、search-similar），每次分析都产生数据沉淀（embedding + Milvus + entities），后续分析可检索历史。

---

## 整体流程

### Backend 定时流程（纯调度）

```
1. fetch_and_save() 拉取新闻并自动落盘（幂等）
2. _scan_pending_news() 扫描待分析新闻（analysis_status 为空、pending 或 failed）
3. 逐个触发 Agent Session 分析
```

### Agent 分析流程（v3）

```
1. update-news --summary        → 概括 + 自动 embedding + Milvus 入库
2. search-similar               → 查找相似历史新闻
3. 事件关联
   ├─ 搜索结果按 event_id 分组
   ├─ LLM 判断：归属已有事件 or 新事件？
   ├─ 新事件：create-event + update-news --event-id
   └─ 已有事件：update-news --event-id + 更新 event.news_ids
4. 读事件历史（仅关联到已有事件时）
   ├─ 读事件的 responses/ 目录
   └─ 了解：之前市场反应了什么
5. 分析 + 预测
   ├─ 结合历史市场反应做分析
   ├─ 生成 prediction（板块 + 个股）
   └─ 写入 prediction.md
6. update-news --analysis       → 写入结构化分析（自动提取 entities）
7. report.md（可选）+ worth_deep_analysis 判断
```

### Backend 后续处理

Agent 完成后 Backend 轮询 news.json 的 `analysis` 字段：

- 追加 `session` 字段（job_id、session_id、context_path）用于追溯
- 读取 `worth_deep_analysis` 决定是否触发深度分析
- 推送分析结果通知

---

## 代码模块

### Backend（调度）

```
src/openclaw_alpha/backend/quick_news/
├── jobs.py          # 定时任务：fetch + scan
├── task_executor.py # 提交 cron + 等待结果 + 通知
└── config.py        # 配置
```

Backend 职责：只管调度和数据创建，不做分析也不操作 Milvus。

### News 模块（数据操作 + CLI）

```
src/openclaw_alpha/news/
├── fetcher/         # 通用新闻拉取（复用 rsshub/akshare，生成 news_id）
├── store.py         # Milvus 集合管理、upsert
├── service.py       # 业务逻辑：fetch_and_save, update_news, search_similar, ...
└── cli.py           # CLI 入口
```

### Core 模块（已有）

```
src/openclaw_alpha/core/
├── milvus/          # 连接管理
└── embedding/       # 向量生成（DashScope text-embedding-v4）
```

---

## analysis 字段（3 字段）

```json
{
  "related_sectors": ["板块1", "板块2"],
  "related_companies": [
    {"name": "公司名", "listed": true, "code": "000001"}
  ],
  "worth_deep_analysis": true
}
```

去掉 `impact_assessment` 和 `reason`：结构化字段只保留机器可用的信息，自然语言描述放在 report.md 中。

---

## 数据目录

```
data/news/{news_id}/
├── news.json        # 元数据 + summary + analysis + entities + session
├── content.md       # 新闻原文
├── prediction.md    # 预测内容（markdown）
└── summary_vector.json   # {"vector": [...]} (1024d)
```

详见 [news-storage.md](news-storage.md)。

---

## 配置

**路径**：`runtime/quick_news/config.yaml`

```yaml
enabled: true
interval_minutes: 30
fetch_limit: 0  # 定时触发时最多处理多少条新闻，0=全部

agent_id: alpha
model: openrouter/qwen/qwen3.6-plus:free

delivery:
  recipients:
    - name: Momojie
      channel: wecom
      agent_id: alpha

cron:
  agent_turn_timeout_seconds: 600
  session_poll_timeout_seconds: 300
  report_wait_timeout_seconds: 300
```

---

## API & CLI

### CLI debug-quick-news

```bash
python -m openclaw_alpha.news.cli debug-quick-news [--limit N]
```

功能同 API，直接在 CLI 触发快速分析流程（拉取 → 扫描 → 提交 cron → 等待结果）。
主要用于无法访问 API 时的调试场景。

---

## 已确认决策

1. **CLI 输出格式**：JSON
2. **去掉 impact_assessment 和 reason**：分析字段精简为 3 字段
3. **news.json 不存 content**：原文存 content.md
4. **embedding.json 独立存储**：news.json 不存向量
5. **统一 Milvus 同步入口**：embedding 存在时自动全量 upsert
6. **事件关联待后续设计**：create-event CLI 暂为占位

---

## 待办

- [ ] 实现 `trigger_deep_analysis` 函数（深度分析模块）
- [ ] 实现 `create-event` CLI 命令
- [ ] 端到端验证完整链路

---

## 相关文档

- [overview.md](overview.md) — 新闻分析系统整体设计
- [news-storage.md](news-storage.md) — 数据结构 + Milvus 同步逻辑
- [news-cli.md](news-cli.md) — CLI 命令手册
- [news-fetcher.md](news-fetcher.md) — 新闻拉取设计
- [deep-analysis.md](deep-analysis.md) — 深度分析设计
- [event-tracking.md](event-tracking.md) — 事件追踪系统设计
