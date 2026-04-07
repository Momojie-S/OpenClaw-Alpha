---
name: openclaw_alpha_news_driven_investment
description: "新闻驱动投资分析，从新闻中发现投资机会。适用于：(1) 新闻热点追踪，(2) 概念题材挖掘，(3) 动态标的筛选。不适用于：纯技术分析、长期价值投资。"
metadata:
  openclaw:
    emoji: "📰"
    requires:
      bins: ["uv"]
---

# 新闻驱动投资分析

从财经新闻中发现投资机会，关联产业分析和标的筛选。

## CLI 工具

所有新闻数据的获取、写入、搜索通过 CLI 完成。完整参数和示例见 [references/cli-reference.md](references/cli-reference.md)，数据源列表见 [references/data-sources.md](references/data-sources.md)。

### 获取

| 命令 | 用途 | 关键输出 |
|------|------|----------|
| `fetch-news` | 拉取新闻并自动落盘 | saved 的新闻包含 `news_id`、`news_dir`、`title`、`link`、`content` |

### 写入（分析时必用）

| 命令 | 用途 | 说明 |
|------|------|------|
| `update-news --summary` | 写入新闻概括 | 自动生成 embedding 并写入 Milvus，**后续可被搜索到** |
| `update-news --analysis` | 写入结构化分析 | 自动提取 entities（板块+公司），用于关键词搜索 |

### 搜索

| 命令 | 用途 |
|------|------|
| `search-similar` | 基于 news_id 的向量搜索，找相似历史新闻 |
| `search-keyword` | 基于 entities 的 BM25 关键词搜索 |

### 查看

| 命令 | 用途 | 关键输出 |
|------|------|----------|
| `get-news` | 查看单条新闻的完整信息 | 包含 `news_dir`（数据目录绝对路径） |
| `get-event` | 查看事件聚合信息 | |

## 写入闭环

**分析即写入 — 每次分析都应通过 CLI 把结果存下来。**

```
分析一条新闻但不写入  =  一次性分析，无法积累
分析一条新闻并写入    =  对知识库的贡献，后续分析可检索
```

为什么写入重要：
- `update-news --summary` → 生成 embedding → Milvus 入库 → 后续 search-similar 能命中
- `update-news --analysis` → 提取 entities → BM25 索引 → 后续 search-keyword 能找到
- 越多新闻被分析和写入，后续分析的上下文越丰富

## 使用场景

### 快速分析

系统化评估新闻价值，识别板块和标的。参考 [任务模板](tasks/quick-news-analysis.md) 了解产出要求。

### 手动分析

用户给一条新闻或 URL → 用 `fetch-news` 或 `get-news` 获取数据 → 分析 → `update-news` 写入结果。

### 追踪线索

`search-similar` 或 `search-keyword` 搜索历史 → `get-news` 查看详情 → 结合新信息形成判断。

## 分析原则

- **投资视角**：不是新闻摘要，是"这对投资有什么影响"
- **预期差优先**：市场共识外的信息才有超额收益
- **多维度交叉**：新闻 + 板块趋势 + 资金流向，单一维度不可靠
- **时效敏感**：新闻价值递减，尽快分析
- **风险意识**：新闻驱动多为短期机会，注意追高风险
