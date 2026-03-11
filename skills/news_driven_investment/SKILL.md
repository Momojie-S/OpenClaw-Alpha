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
# 获取财联社全球资讯（推荐，AKShare 接口）
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source cls_global --limit 10

# 获取财联社电报快讯（RSSHub 接口）
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source cls_telegraph --limit 10

# 获取金十数据快讯（RSSHub 接口）
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source jin10 --limit 10

# 获取华尔街见闻热榜（推荐，RSSHub 接口）
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source wallstreetcn_hot --limit 10

# 获取华尔街见闻资讯（RSSHub 接口）
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source wallstreetcn_news --limit 10

# 获取第一财经简报（RSSHub 接口）
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source yicai_brief --limit 10

# 获取 36氪资讯（RSSHub 接口）
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source 36kr_news --limit 10

# 获取财联社重点资讯
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source cls_important --limit 5

# 获取个股新闻
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source stock --symbol 000001 --limit 5

# 按关键词筛选新闻
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source cls_telegraph --keyword "AI" --limit 10

# 按日期筛选新闻
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source cls_global --date "2026-03-07" --limit 10
```

### 数据源说明

**AKShare 接口**（优先使用）：

| 数据源 | 来源 | 特点 | 推荐度 |
|--------|------|------|:------:|
| `cls_global` | 财联社 | 实时、快速、覆盖广 | ⭐⭐⭐ |
| `cls_important` | 财联社 | 重点精选，数量少 | ⭐⭐ |
| `stock` | 东方财富 | 按股票代码获取个股新闻 | ⭐⭐ |

**RSSHub 接口**（备选）：

| 数据源 | 来源 | 特点 | 推荐度 |
|--------|------|------|:------:|
| `cls_telegraph` | 财联社电报 | 实时快讯，响应快 | ⭐⭐⭐ |
| `jin10` | 金十数据 | 专业金融资讯，更新频繁 | ⭐⭐⭐ |
| `wallstreetcn_hot` | 华尔街见闻热榜 | 最热文章，市场关注度 | ⭐⭐⭐ |
| `wallstreetcn_news` | 华尔街见闻资讯 | 全球市场资讯，专业深度 | ⭐⭐⭐ |
| `yicai_brief` | 第一财经 | 权威财经媒体，覆盖广 | ⭐⭐ |
| `36kr_news` | 36氪 | 科技财经资讯，投资视角 | ⭐⭐ |

完整路由列表：[RSSHub 投资相关路由](docs/references/rsshub/routes.md)

### 筛选参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--keyword` | 关键词筛选（标题和内容匹配） | `--keyword "AI"` |
| `--date` | 日期筛选（YYYY-MM-DD） | `--date "2026-03-07"` |
| `--limit` | 返回数量限制 | `--limit 10` |

---

## 新闻-板块映射表

从新闻关键词快速定位相关板块：

| 新闻关键词 | 相关板块 | 分析要点 |
|-----------|---------|---------|
| AI/算力/英伟达/GPU | CPO概念、液冷、光模块、算力 | 关注板块趋势是否与新闻一致 |
| 脑机接口 | 脑机接口概念 | 政策驱动型，关注地方政策 |
| 航运/集运/欧线 | 航运概念、港口 | 地缘冲突+运价双重驱动 |
| 地缘冲突/中东 | 军工、黄金、原油、航运 | 避险情绪+供需变化 |
| 新能源/电池 | 钠离子电池、固态电池、刀片电池 | 技术路线+政策支持 |
| 半导体/芯片 | 半导体、芯片、MicroLED | 国产替代+周期反转 |
| 机器人 | 人形机器人、减速器 | 产业化进度+订单落地 |
| 医药/医疗 | 医疗器械、创新药 | 政策+产品获批 |

> **提示**：使用 industry_trend 的 `--top-n 100` 获取完整列表，再手动搜索关键词

---

## 分析步骤

### Step 1: 获取新闻

**输入**：新闻源类型

**动作**：运行脚本获取新闻
```bash
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source cls_global --limit 20
```

**输出**：新闻列表（标题、内容、时间、来源）

---

### Step 2: 识别投资线索

**输入**：新闻内容

**动作**：LLM 分析新闻，识别：
- 涉及的产业/概念（参考上方映射表）
- 利好/利空方向
- 可能的受益/受损标的

**关键检查**：
- 新闻是否已被市场消化？
- 板块趋势是否与新闻方向一致？

**输出**：投资线索列表

---

### Step 3: 验证板块趋势

**输入**：投资线索中的板块名称

**动作**：调用产业热度分析，验证板块趋势
```bash
# 获取概念板块热度 TOP 100
uv run --env-file .env python -m openclaw_alpha.skills.industry_trend.industry_trend_processor.industry_trend_processor --category concept --top-n 100
```

**分析要点**：
- `trend` 字段：加热中、降温中、稳定
- `heat_change`：热度环比变化
- **关注背离**：利好新闻 + 板块降温 = 可能的预期差机会

**输出**：板块热度数据

---

### Step 4: 多维度验证

**输入**：确认有热度的板块

**动作**：根据情况选择调用：
```bash
# 市场情绪（判断整体氛围）
uv run --env-file .env python -m openclaw_alpha.skills.market_sentiment.sentiment_processor.sentiment_processor

# 北向资金（外资动向）
uv run --env-file .env python -m openclaw_alpha.skills.northbound_flow.northbound_processor.northbound_processor --top-n 10

# 标的筛选（找具体股票）
uv run --env-file .env python -m openclaw_alpha.skills.stock_screener.screener_processor.screener_processor --strategy volume_breakout --top-n 10
```

**输出**：各维度分析结果

---

### Step 5: 综合分析

**输入**：所有分析结果

**动作**：LLM 综合：
- 新闻影响力度
- 板块趋势（加热/降温）
- 市场情绪配合度
- 资金流向验证

**输出**：投资建议报告

---

## 示例分析流程

### 场景：AI算力需求爆发

```bash
# 1. 获取新闻
uv run --env-file .env python -m openclaw_alpha.skills.news_driven_investment.news_fetcher.news_fetcher --source cls_global --limit 20

# 2. LLM 分析新闻，识别关键词：AI算力、光模块、CPO

# 3. 验证板块趋势（获取 TOP 100 概念，搜索 CPO/液冷）
uv run --env-file .env python -m openclaw_alpha.skills.industry_trend.industry_trend_processor.industry_trend_processor --category concept --top-n 100

# 4. 检查市场情绪
uv run --env-file .env python -m openclaw_alpha.skills.market_sentiment.sentiment_processor.sentiment_processor

# 5. LLM 综合分析，生成投资建议
```

### 实战案例：2026-03-11 英伟达AI基建新闻

**新闻**：英伟达CEO黄仁勋称AI基建需要投资数万亿美元

**验证结果**：
- CPO概念：热度 43.6，降温中（-25.4%）
- 液冷概念：热度 33.4，降温中（-29.8%）

**背离信号**：利好新闻 vs 板块降温 → 可能存在预期差，需进一步观察

---

## 数据传递

中间结果保存在 workspace，供后续分析使用：

```
.openclaw_alpha/news_driven_investment/{date}/
├── keywords.json       # 提取的关键词
├── analysis.md         # 分析报告
└── candidates.json     # 候选标的
```

---

## 注意事项

1. **时效性**：新闻价值随时间递减，及时分析
2. **多维度验证**：综合产业、资金、情绪，不要只看一个维度
3. **风险意识**：新闻驱动往往是短期机会，注意风险
4. **数据源限制**：AKShare 接口可能有频率限制，不要频繁调用
