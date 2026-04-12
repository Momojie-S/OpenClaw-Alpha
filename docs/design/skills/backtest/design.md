# 设计文档 - 策略回测

## 一、技术方案

基于 backtrader 框架实现回测功能。

## 二、数据源

| 数据 | 来源 | 接口 |
|------|------|------|
| 日线数据 | AKShare | `stock_zh_a_hist()` |

## 三、模块划分

```
backtest/scripts/
└── backtest_processor/
    └── backtest_processor.py
```

### backtest_processor

执行回测：
1. 获取日线数据
2. 创建策略实例
3. 运行回测
4. 输出结果

## 四、策略实现

### ma_cross（均线交叉）

参数：
- fast-period：快速均线周期（默认 5）
- slow-period：慢速均线周期（默认 20）

### rsi（RSI 超买超卖）

参数：
- rsi-period：RSI 周期（默认 14）
- rsi-upper：超买阈值（默认 70）
- rsi-lower：超卖阈值（默认 30）

### bollinger（布林带突破）

参数：
- bollinger-period：布林带周期（默认 20）
- bollinger-devfactor：标准差倍数（默认 2.0）

## 五、命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--stock` | 股票代码 | 必需 |
| `--strategy` | 策略名称 | ma_cross |
| `--start-date` | 开始日期 | 一年前 |
| `--end-date` | 结束日期 | 今天 |
| `--cash` | 初始资金 | 100000 |

## 六、输出设计

`.openclaw_alpha/backtest/{date}/backtest.json`

## 七、A 股特殊处理

| 问题 | 当前处理 |
|------|---------|
| 涨跌停 | 未处理 |
| 交易费用 | 佣金 0.03%，印花税 0.1% |
| 除权除息 | 前复权数据 |
| T+1 交易 | 未限制 |
