# 设计文档 - 期权分析

## 一、技术方案

分为情绪分析和市场概况两个功能。

## 二、数据源

| 数据 | 来源 | 接口 |
|------|------|------|
| 期权行情 | AKShare | `option_sina_sse_list_sina()` |

## 三、模块划分

```
option_analysis/scripts/
├── sentiment_processor/       # 情绪分析
│   └── sentiment_processor.py
└── market_overview_processor/ # 市场概况
    └── market_overview_processor.py
```

### sentiment_processor

计算 PCR 和 IV：
- PCR = Put Volume / Call Volume
- IV_ATM = 平值期权隐含波动率

### market_overview_processor

统计各品种成交/持仓：
- ETF 期权（50ETF、300ETF 等）
- 股指期权（沪深300、上证50 等）

## 四、支持的标的

- ETF期权：510050、510300、510500、588000 等
- 股指期权：IO、HO、MO

## 五、命令行参数

**sentiment_processor**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--underlying` | 标的代码 | 510050 |
| `--date` | 日期 | 今天 |

**market_overview_processor**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date` | 日期 | 今天 |
