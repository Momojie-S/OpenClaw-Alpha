# 设计文档 - stock_analysis

## 一、技术方案

通过股票代码/名称查询单只股票的日线行情，计算活跃度和涨跌趋势。

## 二、数据源

| 数据 | 来源 | 优先级 | 说明 |
|------|------|:------:|------|
| 日线行情 | Tushare | 1 | 需要 120 积分 |
| 历史行情 | AKShare | 2 | 免费无限制 |

## 三、模块划分

```
stock_analysis/
├── scripts/
│   └── stock_analysis_processor/
│       ├── __init__.py
│       └── stock_analysis_processor.py  # 入口脚本
└── docs/
    └── spec.md, design.md, decisions.md
```

### Processor

- **入口**：`stock_analysis_processor.py`
- **参数**：
  - `symbol`：股票代码或名称
  - `--date`：查询日期（可选）

### 输出

- 控制台：精简的股票分析结果
- 文件：`.openclaw_alpha/stock-analysis/{日期}/analysis.json`
