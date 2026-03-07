# 每日投资分析流程

> 本指南帮助你使用 OpenClaw-Alpha 进行日常投资分析。

---

## 快速开始

**一键生成市场报告**（推荐）：

```bash
cd /path/to/OpenClaw-Alpha

# 快速版（仅宏观+情绪）
uv run --env-file .env python -m skills.market_overview.scripts.overview_processor.overview_processor --mode quick --auto-fetch

# 完整版（全层次分析）
uv run --env-file .env python -m skills.market_overview.scripts.overview_processor.overview_processor --mode full --auto-fetch
```

`--auto-fetch` 会自动调用其他 skill 获取数据，无需手动运行每个分析。

---

## 分步分析流程

如果你想更精细地控制分析过程，可以按以下步骤操作：

### Step 0: 综合概览（可选）

```bash
# 一键生成完整报告
uv run --env-file .env python -m skills.market_overview.scripts.overview_processor.overview_processor --auto-fetch
```

**输出**：Markdown 格式的综合报告，包含所有层次的分析结果。

---

### Step 1: 宏观 - 判断大势

```bash
# 1. 指数分析
uv run --env-file .env python -m skills.index_analysis.scripts.index_processor.index_processor

# 2. 市场情绪
uv run --env-file .env python -m skills.market_sentiment.scripts.sentiment_processor.sentiment_processor
```

**关注点**：
- 指数涨跌和趋势
- 市场温度（过热/温热/正常/偏冷/过冷）
- 涨跌停数量
- 主力资金流向

---

### Step 2: 中观 - 找方向

```bash
# 1. 板块热度
uv run --env-file .env python -m skills.industry_trend.scripts.industry_trend_processor.industry_trend_processor

# 2. 资金流向
uv run --env-file .env python -m skills.fund_flow_analysis.scripts.fund_flow_processor.fund_flow_processor

# 3. 北向资金
uv run --env-file .env python -m skills.northbound_flow.scripts.northbound_processor.northbound_processor

# 4. 龙虎榜
uv run --env-file .env python -m skills.lhb_tracker.scripts.lhb_processor.lhb_processor
```

**关注点**：
- 哪些行业/概念领涨
- 主力资金在买入哪些板块
- 外资流向（北向资金）
- 游资/机构动向

---

### Step 3: 微观 - 选标的

```bash
# 1. 选股筛选
uv run --env-file .env python -m skills.stock_screener.scripts.screener_processor.screener_processor --min-change 3 --top-n 20

# 2. 个股分析（替换代码）
uv run --env-file .env python -m skills.stock_analysis.scripts.stock_processor.stock_processor --code 000001

# 3. 基本面分析
uv run --env-file .env python -m skills.fundamental_analysis.scripts.fundamental_processor.fundamental_processor --code 000001

# 4. 技术指标
uv run --env-file .env python -m skills.technical_indicators.scripts.technical_processor.technical_processor --code 000001

# 5. 风险检查
uv run --env-file .env python -m skills.risk_alert.scripts.risk_processor.risk_processor --code 000001
```

**关注点**：
- 筛选条件是否符合策略
- 个股基本面是否健康
- 技术面是否出现买卖信号
- 是否有风险提示

---

### Step 4: 事件 - 找催化

```bash
# 1. 新闻驱动
uv run --env-file .env python -m skills.news_driven_investment.scripts.news_processor.news_processor

# 2. 涨停追踪
uv run --env-file .env python -m skills.limit_up_tracker.scripts.limit_up_processor.limit_up_processor

# 3. 公告解读
uv run --env-file .env python -m skills.announcement_analysis.scripts.announcement_processor.announcement_processor --type 业绩预告
```

**关注点**：
- 哪些新闻可能影响股价
- 哪些板块有涨停股（热点）
- 重要公告（业绩、重组等）

---

### Step 5: 组合 - 管持仓

```bash
# 1. 添加自选
uv run --env-file .env python -m skills.watchlist_monitor.scripts.watchlist_processor.watchlist_processor --add 000001

# 2. 查看自选
uv run --env-file .env python -m skills.watchlist_monitor.scripts.watchlist_processor.watchlist_processor --watch

# 3. 持仓分析
uv run --env-file .env python -m skills.portfolio_analysis.scripts.portfolio_processor.portfolio_processor --positions 000001:1000:10.5,600000:500:15.2
```

**关注点**：
- 自选股表现
- 持仓盈亏
- 是否需要调仓

---

## 典型场景

### 场景 1: 早盘准备（9:00-9:30）

```bash
# 快速查看市场状态
uv run --env-file .env python -m skills.market_overview.scripts.overview_processor.overview_processor --mode quick --auto-fetch

# 查看自选股
uv run --env-file .env python -m skills.watchlist_monitor.scripts.watchlist_processor.watchlist_processor --watch

# 查看昨晚公告
uv run --env-file .env python -m skills.announcement_analysis.scripts.announcement_processor.announcement_processor --type 风险提示
```

### 场景 2: 盘中监控（9:30-15:00）

```bash
# 查看板块资金流向
uv run --env-file .env python -m skills.fund_flow_analysis.scripts.fund_flow_processor.fund_flow_processor

# 查看涨停股
uv run --env-file .env python -m skills.limit_up_tracker.scripts.limit_up_processor.limit_up_processor

# 查看北向资金
uv run --env-file .env python -m skills.northbound_flow.scripts.northbound_processor.northbound_processor
```

### 场景 3: 盘后复盘（15:00-17:00）

```bash
# 完整市场报告
uv run --env-file .env python -m skills.market_overview.scripts.overview_processor.overview_processor --mode full --auto-fetch

# 查看龙虎榜
uv run --env-file .env python -m skills.lhb_tracker.scripts.lhb_processor.lhb_processor

# 分析今日热点
uv run --env-file .env python -m skills.news_driven_investment.scripts.news_processor.news_processor
```

---

## 数据存储

所有分析结果保存在 `{workspace}/.openclaw_alpha/` 目录：

```
.openclaw_alpha/
├── index_analysis/
│   └── 2026-03-08/
│       └── index.json
├── market_sentiment/
│   └── 2026-03-08/
│       └── sentiment.json
├── industry_trend/
│   └── 2026-03-08/
│       └── heat.json
└── ...
```

**好处**：
- 避免重复获取数据
- 可以对比历史数据
- market_overview 可以直接读取

---

## 提示

1. **优先使用 `--auto-fetch`**：让 market_overview 自动获取数据，省时省力
2. **善用 `--top-n`**：控制输出数量，节省 token
3. **定期清理**：`.openclaw_alpha/` 目录会积累历史数据，定期清理
4. **指定日期**：所有 processor 支持 `--date` 参数，可以分析历史数据

---

## 参考资料

- [投资分析框架](analysis-framework.md)
- [项目概述](../project-overview.md)
