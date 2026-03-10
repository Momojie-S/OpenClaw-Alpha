# 设计文档 - 市场综合分析

## 一、技术方案

聚合多个 skill 的输出，整合生成综合报告。

## 二、数据源

本 skill 不直接获取数据，而是聚合其他 skill 的输出：

| 数据 | 来源 Skill |
|------|-----------|
| 指数数据 | index_analysis |
| 情绪数据 | market_sentiment |
| 板块数据 | industry_trend |
| 资金流向 | fund_flow_analysis |
| 北向资金 | northbound_flow |

## 三、模块划分

```
market_overview/scripts/
└── overview_processor/
    └── overview_processor.py
```

### overview_processor

聚合其他 skill 的输出，生成综合报告：
1. 读取各 skill 的 JSON 输出
2. 按规则计算综合判断
3. 生成 Markdown 报告

## 四、命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date` | 分析日期 | 今天 |
| `--mode` | quick(快速)/full(完整) | full |
| `--output` | text/json | text |
| `--auto-fetch` | 数据不存在时自动获取 | False |

## 五、输出设计

`.openclaw_alpha/market_overview/{date}/report.json`
