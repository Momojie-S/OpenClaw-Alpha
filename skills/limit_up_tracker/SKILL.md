---
name: openclaw_alpha_limit_up_tracker
description: "涨停追踪：追踪涨停板、连板股、炸板股。适用于：(1) 查看今日涨停股，(2) 筛选连板龙头，(3) 监控炸板风险，(4) 追踪昨日涨停表现。不适用于：涨停预测、实时推送、复杂技术分析。"
metadata:
  openclaw:
    emoji: "📈"
    requires:
      bins: ["uv"]
---

# 涨停追踪

追踪涨停板、连板股、炸板股，把握市场热点和风险信号。

## 使用说明

### 脚本运行

```bash
uv run --env-file .env python skills/limit_up_tracker/scripts/limit_up_fetcher/limit_up_fetcher.py [参数]
```

### 运行记录

运行记录保存在：
- 涨停数据：`.openclaw_alpha/limit_up_tracker/{date}/limit_up.json`
- 跌停数据：`.openclaw_alpha/limit_up_tracker/{date}/limit_down.json`
- 炸板数据：`.openclaw_alpha/limit_up_tracker/{date}/broken.json`

## 分析步骤

### Step 1: 获取今日涨停

**输入**：交易日期

**动作**：运行脚本获取涨停股
```bash
# 默认获取今日涨停
uv run --env-file .env python skills/limit_up_tracker/scripts/limit_up_fetcher/limit_up_fetcher.py

# 指定日期
uv run --env-file .env python skills/limit_up_tracker/scripts/limit_up_fetcher/limit_up_fetcher.py --date "2026-03-07"
```

**输出**：涨停股列表（含连板统计、封板时间、炸板次数等）

---

### Step 2: 筛选连板龙头

**输入**：最小连板数

**动作**：筛选连板股
```bash
# 获取 2 连板以上
uv run --env-file .env python skills/limit_up_tracker/scripts/limit_up_fetcher/limit_up_fetcher.py --min-continuous 2

# 获取 3 连板以上（高连板）
uv run --env-file .env python skills/limit_up_tracker/scripts/limit_up_fetcher/limit_up_fetcher.py --min-continuous 3
```

**输出**：高连板股列表

---

### Step 3: 监控炸板风险

**输入**：炸板类型

**动作**：获取炸板股池
```bash
# 获取今日炸板股
uv run --env-file .env python skills/limit_up_tracker/scripts/limit_up_fetcher/limit_up_fetcher.py --type broken
```

**输出**：炸板股列表（涨停后打开的股票）

---

### Step 4: 追踪昨日涨停表现

**输入**：昨日涨停类型

**动作**：获取昨日涨停今日表现
```bash
# 查看昨日涨停股今日表现
uv run --env-file .env python skills/limit_up_tracker/scripts/limit_up_fetcher/limit_up_fetcher.py --type previous
```

**输出**：昨日涨停股今日涨跌幅、振幅等

---

### Step 5: 监控跌停

**输入**：跌停类型

**动作**：获取跌停股池
```bash
# 获取今日跌停股
uv run --env-file .env python skills/limit_up_tracker/scripts/limit_up_fetcher/limit_up_fetcher.py --type limit_down
```

**输出**：跌停股列表

---

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date` | 交易日期 (YYYY-MM-DD) | 今天 |
| `--type` | 类型：`limit_up`、`limit_down`、`broken`、`previous` | limit_up |
| `--min-continuous` | 最小连板数 | 1 |
| `--top-n` | 返回数量 | 20 |

## 输出字段

| 字段 | 说明 |
|------|------|
| 代码 | 股票代码 |
| 名称 | 股票名称 |
| 连板 | 连续涨停天数 |
| 封板时间 | 首次封板时间（越早越强） |
| 炸板次数 | 当日打开次数（越多越不稳） |
| 封板资金 | 流通市值（越大封板越稳） |
| 所属行业 | 板块分类 |

## 使用场景

### 场景 1：快速了解今日涨停

```
使用者：今天涨停股有哪些？连板股呢？
Agent：运行 limit_up_fetcher，返回涨停列表 + 连板统计
```

### 场景 2：追踪连板龙头

```
使用者：哪些股票 3 连板以上？
Agent：运行 limit_up_fetcher --min-continuous 3
```

### 场景 3：监控炸板风险

```
使用者：今天有没有炸板的？
Agent：运行 limit_up_fetcher --type broken
```

### 场景 4：验证追涨收益

```
使用者：昨天涨停的今天表现怎么样？
Agent：运行 limit_up_fetcher --type previous
```

## 相关 Skill

| Skill | 联动方式 |
|-------|---------|
| industry_trend | 涨停股按行业分类，分析热点板块 |
| lhb_tracker | 涨停股龙虎榜，查看主力资金 |
| stock_screener | 涨停股筛选，进一步分析 |
| market_sentiment | 涨停数量作为市场情绪指标 |

## 注意事项

1. **数据时效**：接口只能获取近 30 个交易日的数据
2. **非交易日**：非交易日返回空数据
3. **封板强度**：封板时间早、炸板次数少、封板资金大 = 封板更稳
4. **风险提示**：高连板股风险较大，追涨需谨慎
