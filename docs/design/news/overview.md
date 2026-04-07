# 新闻分析系统设计

## 概述

两阶段新闻分析系统，从海量快讯中筛选价值内容，逐步深入。

```
海量新闻 → 快速分析（筛选层）→ 深度分析（精炼层）
              ↓                    ↓
         结构化 + 索引          深度洞察 + 建议
```

## 设计原则

### 调度与执行分离

```
┌─────────────────────────────────────────┐
│            调度层 (Backend)              │
│  - Cron：定时拉取 + 触发 Agent           │
│  - API：手动触发（调试）                  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│           执行层 (Agent Session)         │
│  - Agent 通过 CLI 写入分析数据           │
│  - 拥有 openclaw_alpha_* 全部 skill      │
└─────────────────────────────────────────┘
```

### 两阶段漏斗

| 维度 | 快速分析 | 深度分析 |
|------|----------|----------|
| 处理量 | 全量新新闻 | 筛选后（<5%） |
| 目标 | 结构化 + 初判 | 深度洞察 + 建议 |
| 输出 | news.json（CLI 写入） | report.md |
| 触发 | 定时拉取 | worth_deep_analysis=true |
| 耗时 | 秒级/条 | 分钟级/条 |

### 分析即写入

Agent 通过 CLI 操作数据，每次分析产生数据沉淀：
- `update-news --summary` → embedding + Milvus 入库
- `update-news --analysis` → entities + BM25 索引
- 后续分析可检索历史上下文，越分析越智能

---

## 实现状态

| 模块 | 状态 | 说明 |
|------|------|------|
| 新闻拉取 | ✅ 已实现 | 多源拉取（AKShare + RSSHub）+ 幂等落盘 |
| CLI + Service | ✅ 已实现 | 7 个命令：fetch/update/search/get |
| Milvus 存储 | ✅ 已实现 | 向量搜索 + BM25 关键词搜索 |
| Backend 调度 | ✅ 已实现 | 定时拉取 + analysis_status 追踪 |
| Agent 任务模板 | ✅ v2 已实现 | CLI 写入闭环 |
| 深度分析 | ⏳ 待实现 | TODO |

---

## 代码结构

```
src/openclaw_alpha/
├── backend/quick_news/
│   ├── jobs.py              # 定时任务：fetch + scan + trigger
│   ├── task_executor.py     # 提交 cron + 等待结果 + 通知
│   └── config.py            # 配置
├── news/
│   ├── fetcher/             # 通用新闻拉取（AKShare + RSSHub）
│   ├── store.py             # Milvus 集合管理
│   ├── service.py           # 业务逻辑层
│   └── cli.py               # CLI 入口
└── core/
    ├── milvus/              # 连接管理
    └── embedding/           # 向量生成
```

**配置文件**：`workspace/quick_news/config.yaml`

---

## 输出结构

```
data/news/{news_id}/
├── news.json        # 元数据 + summary + analysis + entities + session
├── content.md       # 新闻原文
└── embedding.json   # 向量数据
```

---

## 相关文档

- [quick-analysis.md](quick-analysis.md) — 快速分析详细设计
- [deep-analysis.md](deep-analysis.md) — 深度分析设计
- [news-storage.md](news-storage.md) — 数据结构 + Milvus 同步
- [news-cli.md](news-cli.md) — CLI 命令手册
- [news-fetcher.md](news-fetcher.md) — 新闻拉取设计
- [event-tracking-storage.md](event-tracking-storage.md) — 事件跟踪存储设计
