# 设计文档 - 智能定投策略

## 一、技术方案

基于股债性价比指标，计算定投倍数建议。

## 二、数据源

| 数据 | 来源 | 接口 |
|------|------|------|
| 沪深300 PE | Tushare | `daily_basic()` |
| 10Y 国债收益率 | Tushare | `shibor_quote()` |

## 三、模块划分

```
smart_dip/scripts/
├── dip_advice_processor/
│   └── dip_advice_processor.py
└── dip_history_processor/
    └── dip_history_processor.py
```

### dip_advice_processor

计算定投建议：
1. 获取沪深300 PE
2. 获取 10Y 国债收益率
3. 计算股债性价比
4. 查表得出定投倍数

### dip_history_processor

分析历史定投记录：
- 历史倍数
- 累计金额

## 四、命令行参数

**dip_advice_processor**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date` | 分析日期 | 今天 |
| `--base-amount` | 基准金额 | 1000 |
| `--strategy` | 策略 | fed_model |

**dip_history_processor**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--months` | 回看月数 | 12 |
| `--base-amount` | 基准金额 | 1000 |

## 五、输出设计

`.openclaw_alpha/smart_dip/{date}/dip_advice.json`
