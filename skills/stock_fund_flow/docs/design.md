# 设计文档 - stock_fund_flow

## 一、技术方案

直接使用 AKShare 获取东方财富的资金流向数据，无需单独 Fetcher（数据源单一）。

**数据来源**：东方财富（稳定但有延迟）

## 二、数据源

| 数据 | 来源 | 接口 |
|------|------|------|
| 个股资金流向 | AKShare | `stock_individual_fund_flow()` |

**数据范围**：约 120 个交易日

## 三、模块划分

```
stock_fund_flow/
├── scripts/
│   └── stock_fund_flow_processor/  # 资金流向分析
│       └── stock_fund_flow_processor.py
└── docs/
```

### stock_fund_flow_processor

**职责**：分析个股资金流向

**输入**：股票代码、汇总周期、趋势分析回看天数

**输出**：
- 资金流向汇总（今日/近5日/近10日/近20日）
- 资金趋势判断
- 资金与价格关联

## 四、接口契约

```bash
uv run --env-file .env python skills/stock_fund_flow/scripts/stock_fund_flow_processor/stock_fund_flow_processor.py <symbol> [--periods 1 5 10 20] [--lookback 10] [--output text|json]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| symbol | 股票代码 | 必填 |
| --periods | 汇总周期 | 1 5 10 20 |
| --lookback | 趋势分析回看天数 | 10 |
| --output | 输出格式 | text |

## 五、信号输出

**路径**：`.openclaw_alpha/signals/flow/{symbol}/main_flow.json`

**信号类型**：main_flow（主力资金）
