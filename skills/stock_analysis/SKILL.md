---
name: openclaw_alpha_stock_analysis
description: "个股分析工具。适用于：(1) 查询单只股票的行情数据，(2) 了解股票的成交活跃度，(3) 快速判断股票涨跌趋势。不适用于：港股/美股、深度财务分析、技术指标分析。"
metadata:
  openclaw:
    emoji: "📈"
    requires:
      bins: ["uv"]
---

# 个股分析

快速获取单只 A 股股票的核心指标和市场表现。

## 使用说明

### 脚本运行

```bash
# 查询指定股票
uv run --env-file .env python skills/stock_analysis/scripts/stock_analysis_processor/stock_analysis_processor.py <股票代码或名称> [--date YYYY-MM-DD]

# 示例
uv run --env-file .env python skills/stock_analysis/scripts/stock_analysis_processor/stock_analysis_processor.py 000001
uv run --env-file .env python skills/stock_analysis/scripts/stock_analysis_processor/stock_analysis_processor.py 平安银行 --date 2026-03-06
```

### 运行记录

分析结果保存在 `.openclaw_alpha/stock-analysis/{日期}/analysis.json`

## 分析步骤

### Step 1: 获取股票数据

**输入**：
- 股票代码（如 000001）或名称（如 平安银行）
- 日期（可选，默认最近交易日）

**动作**：
```bash
uv run --env-file .env python skills/stock_analysis/scripts/stock_analysis_processor/stock_analysis_processor.py <股票标识> [--date YYYY-MM-DD]
```

**输出**：
- 价格指标（开盘、最高、最低、收盘、涨跌幅）
- 成交指标（成交量、成交额）
- 分析结论（活跃度、涨跌趋势）

### 输出示例

```json
{
  "code": "000001.SZ",
  "name": "平安银行",
  "date": "2026-03-06",
  "price": {
    "open": 10.78,
    "high": 10.84,
    "low": 10.77,
    "close": 10.82,
    "pre_close": 10.81,
    "change": 0.01,
    "pct_change": 0.09
  },
  "volume": {
    "volume": 47657680,
    "amount": 514733550,
    "turnover_rate": 0.0
  },
  "analysis": {
    "activity": "不活跃",
    "trend": "持平"
  }
}
```

## 分析规则

### 活跃度判断

| 换手率 | 结论 |
|--------|------|
| > 10% | 非常活跃 |
| > 5% | 较活跃 |
| > 2% | 正常 |
| <= 2% | 不活跃 |

### 涨跌判断

| 涨跌幅 | 结论 |
|--------|------|
| > 5% | 大涨 |
| > 2% | 上涨 |
| < -5% | 大跌 |
| < -2% | 下跌 |
| 其他 | 持平 |

## 数据源

- **Tushare**（优先）：日线行情，需要 120 积分
- **AKShare**（备选）：历史行情，无积分要求

## 后续版本

- V1.1：估值指标（PE、PB）
- V1.2：行业对比
- V1.3：历史趋势
