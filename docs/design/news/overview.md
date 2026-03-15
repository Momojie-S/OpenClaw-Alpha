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
│  - Cron：定时拉取 + 触发智能体            │
│  - API：手动触发（调试）                  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│           执行层 (Agent Session)         │
│  - 智能体执行分析任务                     │
│  - 掌握 openclaw_alpha_* 全部 skill      │
└─────────────────────────────────────────┘
```

### 两阶段漏斗

| 维度 | 快速分析 | 深度分析 |
|------|----------|----------|
| 处理量 | 全量新新闻 | 筛选后（<5%） |
| 目标 | 结构化 + 初判 | 深度洞察 + 建议 |
| 输出 | analysis.json | report.md |
| 触发 | 定时拉取 | worth_deep_analysis=true |
| 耗时 | 秒级/条 | 分钟级/条 |

---

## 实现状态

| 模块 | 状态 | 说明 |
|------|------|------|
| RSS 拉取 | ✅ 已实现 | 多实例 fallback |
| 状态管理 | ✅ 已实现 | 按日期防重 |
| 快速分析 | ✅ 已实现 | Agent Session 执行 |
| 深度分析 | ⏳ 待实现 | TODO in task_executor.py |

---

## 代码结构

```
src/openclaw_alpha/backend/quick_news/
├── config.py           # 配置模型
├── jobs.py             # 定时任务：fetch_all_quick_news()
├── rss_fetcher.py      # RSS 拉取
├── state_manager.py    # 状态管理
├── task_executor.py    # 提交分析任务
└── models.py           # 数据模型
```

**配置文件**：`workspace/quick_news/config.yaml`

---

## 输出结构

```
workspace/quick_news_analysis/{date}/{news_id}/
├── analysis.json       # 结构化分析结果
└── report.md           # 详细报告（可选）
```

---

## 相关文档

- [quick-analysis.md](quick-analysis.md) - 快速分析详细设计
- [../../../skills/news_driven_investment/tasks/quick-news-analysis.md](../../../skills/news_driven_investment/tasks/quick-news-analysis.md) - 任务模板
