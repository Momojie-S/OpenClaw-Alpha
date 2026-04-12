# 设计文档 - fundamental_analysis

## 一、技术方案

从东方财富获取财务指标，从百度股市通获取估值数据，计算四维度评分并综合评级。

## 二、数据源

| 数据 | 来源 | 接口 |
|------|------|------|
| 财务指标 | AKShare | `stock_financial_analysis_indicator_em`（东方财富） |
| 估值数据 | AKShare | `stock_zh_valuation_baidu`（百度股市通） |

## 三、模块划分

```
fundamental_analysis/
├── scripts/
│   └── fundamental_processor/
│       ├── __init__.py
│       └── fundamental_processor.py  # 入口脚本
└── docs/
```

### Processor

- **入口**：`fundamental_processor.py`
- **参数**：
  - `--code`：股票代码（必填）
  - `--include-history`：是否包含估值历史

### 输出

- 控制台：JSON 格式分析结果
- 文件：`.openclaw_alpha/fundamental_analysis/{date}/{code}.json`

## 四、注意事项

- 行业差异：不同行业估值标准不同
- 周期性：周期性行业需看完整周期
- 新股：上市不足 1 年可能缺少历史数据
