# 设计文档 - 风险监控

## 一、技术方案

采用多维度风险检测：
- 业绩风险：查询业绩预告数据
- 价格风险：查询日线数据，计算连续下跌
- 资金风险：查询资金流向，计算持续流出

## 二、数据源

| 数据 | 来源 | 接口 |
|------|------|------|
| 业绩预告 | AKShare | `stock_em_yjyg()` |
| 日线数据 | AKShare | `stock_zh_a_hist()` |
| 资金流向 | AKShare | `stock_individual_fund_flow()` |

## 三、模块划分

```
risk_alert/scripts/
├── forecast_fetcher/       # 业绩预告获取
│   ├── forecast_fetcher.py
│   └── akshare.py
└── risk_processor/         # 风险检查处理
    └── risk_processor.py
```

### forecast_fetcher

获取业绩预告数据，解析预告类型。

### risk_processor

聚合多维度风险检测：
1. 调用 forecast_fetcher 获取业绩风险
2. 调用 AKShare 获取日线数据，检测价格风险
3. 调用 AKShare 获取资金流向，检测资金风险
4. 综合评级，输出建议

## 四、命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `symbol` | 股票代码（单股） | - |
| `--date` | 检查日期 | 今天 |
| `--days` | 检查近 N 天 | 5 |
| `--batch` | 批量检查（逗号分隔） | - |
| `--batch-file` | 从文件读取 | - |
| `--watchlist` | 从自选股读取 | False |
| `--output` | 保存结果 | False |

## 五、输出设计

**单股检查**：`.openclaw_alpha/risk_alert/{date}/risk_check.json`

**批量扫描**：`.openclaw_alpha/risk_alert/{date}/batch_risk_scan.json`
