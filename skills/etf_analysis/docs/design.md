# 设计文档 - etf_analysis

## 一、技术方案

从新浪财经获取 ETF 行情数据，支持筛选、排序和历史查询。

## 二、数据源

| 数据 | 来源 | 说明 |
|------|------|------|
| ETF 行情 | AKShare | 新浪财经数据，稳定可靠 |

## 三、模块划分

```
etf_analysis/
├── scripts/
│   └── etf_processor/
│       ├── __init__.py
│       └── etf_processor.py  # 入口脚本
└── docs/
```

### Processor

- **入口**：`etf_processor.py`
- **参数**：
  - `--action`：`spot`（实时行情）或 `history`（历史数据）
  - `--symbol`：ETF 代码（history 必填）
  - `--change-min/max`：涨跌幅范围
  - `--amount-min`：成交额下限
  - `--keyword`：名称关键词
  - `--sort-by`：排序字段
  - `--top-n`：返回数量
  - `--days`：历史天数

### 输出

- 行情数据：`.openclaw_alpha/etf_analysis/{date}/spot.json`
- 历史数据：`.openclaw_alpha/etf_analysis/{date}/history_{symbol}.json`

## 四、注意事项

- ETF 代码格式：`sz159915`（深市）或 `sh510300`（沪市）
- 成交额单位自动转换为亿元
- 非交易日返回上一交易日数据
