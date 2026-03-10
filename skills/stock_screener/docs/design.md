# 设计文档 - stock_screener

## 一、技术方案

从东方财富获取全市场行情数据，按条件筛选并排序返回结果。

## 二、数据源

| 数据 | 来源 | 说明 |
|------|------|------|
| 全市场行情 | AKShare | 东方财富数据，免费 |

## 三、模块划分

```
stock_screener/
├── scripts/
│   └── screener_processor/
│       ├── __init__.py
│       └── screener_processor.py  # 入口脚本
└── docs/
```

### Processor

- **入口**：`screener_processor.py`
- **参数**：
  - `--strategy`：预设策略名称
  - `--change-min/max`：涨跌幅范围
  - `--turnover-min/max`：换手率范围
  - `--amount-min/max`：成交额范围
  - `--cap-min/max`：市值范围
  - `--sort`：排序字段
  - `--top-n`：返回数量

### 输出

- 控制台：JSON 格式筛选结果
- 文件：`.openclaw_alpha/stock-screener/{date}/screener.json`
