---
name: openclaw_alpha_etf_analysis
description: "ETF 分析：获取 ETF 实时行情、筛选排序、历史数据。适用于：(1) 查看 ETF 行情排行，(2) 筛选符合条件的 ETF，(3) 查看单个 ETF 历史走势。不适用于：ETF 持仓分析、折溢价分析、ETF 推荐。"
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["uv"]
---

# ETF 分析

获取 ETF 实时行情、筛选排序、查看历史走势。

## 使用说明

### 脚本运行

```bash
uv run --env-file .env python -m openclaw_alpha.skills.etf_analysis.etf_processor.etf_processor [参数]
```

### 运行记录

运行记录保存在：
- 行情数据：`.openclaw_alpha/etf_analysis/{date}/spot.json`
- 历史数据：`.openclaw_alpha/etf_analysis/{date}/history_{symbol}.json`

## 分析步骤

### Step 1: 查看今日 ETF 行情

**输入**：无（默认获取今日涨幅榜）

**动作**：运行脚本获取实时行情
```bash
# 默认返回涨幅 Top 20
uv run --env-file .env python -m openclaw_alpha.skills.etf_analysis.etf_processor.etf_processor

# 指定返回数量
uv run --env-file .env python -m openclaw_alpha.skills.etf_analysis.etf_processor.etf_processor --top-n 10
```

**输出**：ETF 行情列表（含代码、名称、价格、涨跌幅、成交额）

---

### Step 2: 筛选 ETF

**输入**：筛选条件

**动作**：按条件筛选 ETF
```bash
# 筛选涨幅 > 2% 且成交额 > 5 亿
uv run --env-file .env python -m openclaw_alpha.skills.etf_analysis.etf_processor.etf_processor \
    --change-min 2 --amount-min 5

# 筛选跌幅 ETF（跌 3% 以上）
uv run --env-file .env python -m openclaw_alpha.skills.etf_analysis.etf_processor.etf_processor \
    --change-max -3

# 按关键词搜索（如创业板相关）
uv run --env-file .env python -m openclaw_alpha.skills.etf_analysis.etf_processor.etf_processor \
    --keyword "创业板"
```

**输出**：符合条件的 ETF 列表

---

### Step 3: 排序 ETF

**输入**：排序字段

**动作**：按指定字段排序
```bash
# 按成交额排序
uv run --env-file .env python -m openclaw_alpha.skills.etf_analysis.etf_processor.etf_processor \
    --sort-by amount --top-n 10

# 按价格排序
uv run --env-file .env python -m openclaw_alpha.skills.etf_analysis.etf_processor.etf_processor \
    --sort-by price --top-n 10
```

**输出**：排序后的 ETF 列表

---

### Step 4: 查看历史数据

**输入**：ETF 代码

**动作**：获取历史走势
```bash
# 获取创业板 ETF 近 30 天历史数据
uv run --env-file .env python -m openclaw_alpha.skills.etf_analysis.etf_processor.etf_processor \
    --action history --symbol sz159915

# 指定天数
uv run --env-file .env python -m openclaw_alpha.skills.etf_analysis.etf_processor.etf_processor \
    --action history --symbol sz159915 --days 60
```

**输出**：历史数据列表（日期、开盘价、最高价、最低价、收盘价、成交量）

---

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--action` | 操作：`spot`(实时行情)、`history`(历史数据) | spot |
| `--symbol` | ETF 代码（history 必填） | - |
| `--change-min` | 涨跌幅下限 (%) | - |
| `--change-max` | 涨跌幅上限 (%) | - |
| `--amount-min` | 成交额下限（亿） | - |
| `--keyword` | 名称关键词 | - |
| `--sort-by` | 排序字段：`change`、`amount`、`price` | change |
| `--top-n` | 返回数量 | 20 |
| `--days` | 历史天数（history 模式） | 30 |

## 输出字段

### 实时行情

| 字段 | 说明 |
|------|------|
| code | ETF 代码 |
| name | ETF 名称 |
| price | 最新价 |
| change_pct | 涨跌幅 (%) |
| change | 涨跌额 |
| amount | 成交额（亿） |
| volume | 成交量 |

### 历史数据

| 字段 | 说明 |
|------|------|
| date | 日期 |
| open | 开盘价 |
| high | 最高价 |
| low | 最低价 |
| close | 收盘价 |
| volume | 成交量 |
| amount | 成交额（亿） |

## 使用场景

### 场景 1：懒人查看今日 ETF 行情

```
使用者：今天 ETF 表现怎么样？
Agent：运行 etf_processor，返回涨幅 Top 20
```

### 场景 2：寻找热门 ETF

```
使用者：今天成交额大的 ETF 有哪些？
Agent：运行 etf_processor --sort-by amount --top-n 10
```

### 场景 3：追踪特定板块 ETF

```
使用者：医药相关的 ETF 有哪些？
Agent：运行 etf_processor --keyword "医药"
```

### 场景 4：分析 ETF 走势

```
使用者：创业板 ETF 最近走势怎么样？
Agent：运行 etf_processor --action history --symbol sz159915 --days 30
```

## 相关 Skill

| Skill | 联动方式 |
|-------|---------|
| index_analysis | 指数分析，ETF 跟踪指数 |
| stock_screener | 选股筛选，ETF 持仓股票 |
| market_sentiment | 市场情绪，ETF 涨跌作为参考 |
| watchlist_monitor | 自选股监控，可添加 ETF 到自选 |

## 注意事项

1. **数据源**：使用新浪财经数据，稳定可靠
2. **非交易日**：非交易日返回的数据为上一交易日
3. **ETF 代码**：格式为 `sz159915`（深市）或 `sh510300`（沪市）
4. **成交额单位**：自动转换为亿元，方便阅读
