# 设计文档 - 融资融券分析

## 一、技术方案

分为市场汇总和个股排行两个独立功能。

## 二、数据源

| 数据 | 来源 | 接口 |
|------|------|------|
| 市场融资融券 | AKShare | `stock_margin_detail_szsh()` |
| 个股融资融券 | AKShare | `stock_margin_detail()` |

## 三、模块划分

```
margin_trading/scripts/
├── market_margin_processor/    # 市场汇总
│   └── market_margin_processor.py
└── stock_margin_processor/     # 个股排行
    └── stock_margin_processor.py
```

### market_margin_processor

查询沪深两市融资融券汇总数据：
- 沪市融资余额
- 深市融资余额
- 环比变化
- 杠杆水平判断

### stock_margin_processor

查询个股融资融券排行：
- 融资余额 Top N
- 融券余额 Top N

## 四、命令行参数

**market_margin_processor**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date` | 查询日期 | 最新交易日 |
| `--output` | 输出格式：text/json | text |

**stock_margin_processor**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--type` | 类型：financing/securities | financing |
| `--top-n` | 返回数量 | 20 |
| `--date` | 查询日期 | 最新交易日 |

## 五、输出设计

**市场汇总**：`.openclaw_alpha/margin_trading/{date}/market_margin.json`

**个股排行**：`.openclaw_alpha/margin_trading/{date}/stock_margin.json`
