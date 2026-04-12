# 设计文档 - 资金流向分析

## 一、技术方案

使用 AKShare 的同花顺资金流向接口。

## 二、数据源

| 数据 | 来源 | 接口 |
|------|------|------|
| 行业资金流向 | AKShare | `stock_board_concept_fund_flow_em()` |
| 概念资金流向 | AKShare | `stock_board_industry_fund_flow_em()` |

## 三、模块划分

```
fund_flow_analysis/scripts/
└── fund_flow_processor/
    └── fund_flow_processor.py
```

### fund_flow_processor

获取资金流向数据：
- 支持行业和概念两种类型
- 支持多时间周期
- 支持排序和筛选

## 四、命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--type` | 类型：industry/concept | industry |
| `--period` | 时间周期 | 今日 |
| `--sort-by` | 排序：net/change/inflow | net |
| `--min-net` | 最小净额过滤(亿) | 不过滤 |
| `--top-n` | 返回数量 | 10 |

## 五、输出设计

`.openclaw_alpha/fund_flow_analysis/{date}/fund_flow.json`

## 六、注意

- 数据来源：同花顺（稳定但可能有延迟）
- 资金净额单位：亿元
