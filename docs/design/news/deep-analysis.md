# 深度分析设计

## 概述

深度分析是新闻分析系统的第二层，以**事件**为单位，对快速分析标记为重要的事件进行多维度深入分析。

---

## 触发机制

### event.json 新增字段

```json
{
  "needs_deep_analysis": true,
  "deep_analysis": {
    "analyzed_news_count": 1,
    "analyzed_at": "2026-04-09T08:00:00+08:00"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `needs_deep_analysis` | bool | 是否需要深度分析。快速分析时置 true，深度分析完成后由 backend 置 false |
| `deep_analysis` | object\|null | 记录上次深度分析的覆盖范围，null 表示从未分析过 |
| `deep_analysis.analyzed_news_count` | int | 上次深度分析时事件关联的新闻数量 |
| `deep_analysis.analyzed_at` | string | 上次深度分析完成时间（ISO 8601） |

### 判断逻辑

```
event.status == "ongoing"
  AND event.needs_deep_analysis == true
  AND len(event.news_ids) > (event.deep_analysis?.analyzed_news_count ?? 0)
  → 需要执行深度分析
```

利用 news_ids 线性追加的特性，用计数差即可判断是否有新新闻。

### 流程

```
快速分析阶段:
  每条新闻 → worth_deep_analysis=true
          → 关联事件时 event.needs_deep_analysis = true

快速分析完成后:
  list-events --needs-deep
  过滤: len(news_ids) > analyzed_news_count
  → 逐事件执行深度分析

深度分析（backend 自动更新）:
  分析完成后 → analyzed_news_count = len(news_ids)
             → needs_deep_analysis = false
```

### 边界情况

| 场景 | 处理 |
|------|------|
| 新事件无 deep_analysis | null 视为 count=0，自动触发 |
| 已关闭事件 | status=closed 不参与扫描 |
| 多条新闻连续关联 | needs_deep_analysis 幂等，只需置一次 true |
| 深度分析过程中新新闻 | 分析完写 count，新新闻下次触发 |

---

## 产出

深度分析报告存放在事件目录下：

```
runtime/data/events/{event_id}/
├── event.json
├── deep_analysis/
│   └── 20260410.md      # 日期命名，自然排序
└── responses/            # 已有
```

---

## 分析内容

深度分析面向事件的**全部**已关联新闻（不仅是新增的），因为新信息可能改变对旧信息的理解。

多维度分析包括但不限于：板块趋势、资金流向、技术指标、基本面分析、政策影响、历史对比、行业链条、风险因素、关联标的等。每步分析后，考虑是否有其他需深入的方向。

---

## CLI 变更

| 命令 | 变更 |
|------|------|
| `create-event` | 初始化 `needs_deep_analysis: false`, `deep_analysis: null` |
| `update-news --event-id` | 关联到已有事件时自动置 `needs_deep_analysis: true` |
| `list-events` | 新增 `--needs-deep` 过滤 |

deep_analysis 字段的更新由 backend service 内部完成，不暴露 CLI。
