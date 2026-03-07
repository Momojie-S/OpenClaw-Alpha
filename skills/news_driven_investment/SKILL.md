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

从财经新闻中发现投资机会，自动关联产业分析和标的筛选。

## 使用说明

### 获取新闻

```bash
# 获取财联社全球资讯（推荐）
uv run --env-file .env python -m skills.news_driven_investment.scripts.news_fetcher.news_fetcher --source cls_global --limit 10

# 获取财联社重点资讯
uv run --env-file .env python -m skills.news_driven_investment.scripts.news_fetcher.news_fetcher --source cls_important --limit 5

# 获取个股新闻
uv run --env-file .env python -m skills.news_driven_investment.scripts.news_fetcher.news_fetcher --source stock --symbol 000001 --limit 5

# 按关键词筛选新闻
uv run --env-file .env python -m skills.news_driven_investment.scripts.news_fetcher.news_fetcher --source cls_global --keyword "AI" --limit 10

# 按日期筛选新闻
uv run --env-file .env python -m skills.news_driven_investment.scripts.news_fetcher.news_fetcher --source cls_global --date "2026-03-07" --limit 10
```

### 数据源说明

**AKShare 接口**（脚本内置）：

| 数据源 | 来源 | 特点 | 推荐度 |
|--------|------|------|:------:|
| `cls_global` | 财联社 | 实时、快速、覆盖广 | ⭐⭐⭐ |
| `cls_important` | 财联社 | 重点精选，数量少 | ⭐⭐ |
| `stock` | 东方财富 | 按股票代码获取个股新闻 | ⭐⭐ |

### 筛选参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--keyword` | 关键词筛选（标题和内容匹配） | `--keyword "AI"` |
| `--date` | 日期筛选（YYYY-MM-DD） | `--date "2026-03-07"` |
| `--limit` | 返回数量限制 | `--limit 10` |

**RSSHub 公共实例**（备选）：

```bash
# 财联社电报（实时快讯）
curl -s "https://rsshub.ktachibana.party/cls/telegraph"
```

更多可用实例见 [RSSHub 实例列表](../../../docs/references/rsshub/instances.md)

---

## 分析步骤

### Step 1: 获取新闻

**输入**：新闻源类型

**动作**：运行脚本获取新闻
```bash
uv run --env-file .env python -m skills.news_driven_investment.scripts.news_fetcher.news_fetcher --source cls_global --limit 20
```

**输出**：新闻列表（标题、内容、时间、来源）

---

### Step 2: 识别投资线索

**输入**：新闻内容

**动作**：LLM 分析新闻，识别：
- 涉及的产业/概念
- 利好/利空方向
- 可能的受益/受损标的

**输出**：投资线索列表

---

### Step 3: 调用分析工具

**输入**：投资线索

**动作**：根据线索类型，选择调用其他 Skill：
- `industry_trend` - 产业热度分析
- `stock_screener` - 标的筛选
- `northbound_flow` - 资金流向
- `market_sentiment` - 市场情绪

**输出**：各维度分析结果

---

### Step 4: 综合分析

**输入**：所有分析结果

**动作**：LLM 综合：
- 新闻影响
- 产业热度
- 标的基本面
- 市场情绪
- 资金流向

**输出**：投资建议报告

---

## 数据传递

中间结果保存在 workspace，供后续分析使用：

```
.openclaw_alpha/news_driven_investment/{date}/
├── keywords.json       # 提取的关键词
├── analysis.md         # 分析报告
└── candidates.json     # 候选标的
```

使用 `news_helper.py` 管理中间数据：
```bash
# 保存关键词
uv run --env-file .env python -m skills.news_driven_investment.scripts.news_helper --action save_keywords --keywords "AI" "算力" "光模块"

# 读取关键词
uv run --env-file .env python -m skills.news_driven_investment.scripts.news_helper --action load_keywords
```

---

## 示例分析流程

### 场景：AI算力需求爆发

```bash
# 1. 获取新闻
uv run --env-file .env python -m skills.news_driven_investment.scripts.news_fetcher.news_fetcher --source cls_global --limit 20

# 2. LLM 分析新闻，识别关键词：AI算力、光模块、CPO

# 3. 调用产业热度分析
uv run --env-file .env python -m skills.industry_trend.scripts.industry_trend_processor.industry_trend_processor --category concept --top-n 10

# 4. 调用标的筛选
uv run --env-file .env python -m skills.stock_screener.scripts.screener_processor.screener_processor --strategy volume_breakout --top-n 10

# 5. LLM 综合分析，生成投资建议
```

---

## 注意事项

1. **时效性**：新闻价值随时间递减，及时分析
2. **多维度验证**：综合产业、资金、情绪，不要只看一个维度
3. **风险意识**：新闻驱动往往是短期机会，注意风险
4. **数据源限制**：AKShare 接口可能有频率限制，不要频繁调用
