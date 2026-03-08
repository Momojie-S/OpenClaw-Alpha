---
name: openclaw_alpha_backtest
description: "策略回测功能，验证投资策略的历史表现。适用于：(1) 测试均线交叉策略，(2) 评估策略收益率和风险指标，(3) 分析历史交易记录。不适用于：多股票组合回测、参数优化、实时策略。"
metadata:
  openclaw:
    emoji: "📈"
    requires:
      bins: ["uv"]
---

# 策略回测

验证投资策略的历史表现，评估风险收益指标。

---

## 使用说明

### 脚本运行

```bash
# 基础用法：回测平安银行（000001）
uv run --env-file .env python -m skills.backtest.scripts.backtest_processor.backtest_processor \
    --stock 000001

# 指定日期范围
uv run --env-file .env python -m skills.backtest.scripts.backtest_processor.backtest_processor \
    --stock 000001 \
    --start-date 2025-01-01 \
    --end-date 2026-01-01

# 自定义策略参数（均线交叉）
uv run --env-file .env python -m skills.backtest.scripts.backtest_processor.backtest_processor \
    --stock 000001 \
    --fast-period 10 \
    --slow-period 30

# 自定义初始资金
uv run --env-file .env python -m skills.backtest.scripts.backtest_processor.backtest_processor \
    --stock 000001 \
    --cash 500000

# 安静模式（只输出结果）
uv run --env-file .env python -m skills.backtest.scripts.backtest_processor.backtest_processor \
    --stock 000001 \
    --quiet

# 指定输出文件
uv run --env-file .env python -m skills.backtest.scripts.backtest_processor.backtest_processor \
    --stock 000001 \
    --output .temp/backtest_result.json
```

### 运行记录

回测结果自动保存到 `.openclaw_alpha/backtest/{YYYY-MM-DD}/backtest.json`。

---

## 分析步骤

### Step 1: 选择股票和策略

**输入**：股票代码、策略名称、日期范围

**动作**：运行回测脚本

```bash
uv run --env-file .env python -m skills.backtest.scripts.backtest_processor.backtest_processor \
    --stock 000001 \
    --strategy ma_cross \
    --start-date 2025-03-01 \
    --end-date 2026-03-01
```

**输出**：回测配置信息和运行过程

### Step 2: 查看回测结果

**输出指标**：

| 指标 | 说明 |
|------|------|
| 总收益率 | 策略总收益 / 初始资金 |
| 年化收益率 | 按年计算的收益率 |
| 夏普比率 | 风险调整后收益 |
| 最大回撤 | 从高点到低点的最大跌幅 |
| 总交易次数 | 总买卖次数 |
| 胜率 | 盈利交易占比 |

**示例输出**：

```json
{
  "stock_code": "000001",
  "strategy": "MACrossStrategy",
  "start_date": "2025-03-01",
  "end_date": "2026-03-01",
  "initial_cash": 100000.0,
  "final_value": 115234.56,
  "performance": {
    "total_return": 15.23,
    "annual_return": 15.23,
    "sharpe_ratio": 1.45,
    "max_drawdown": 8.32,
    "total_trades": 12,
    "win_rate": 58.33
  }
}
```

### Step 3: 分析交易记录

完整结果保存在 JSON 文件中，包含所有交易细节。

---

## 可用策略

### ma_cross（均线交叉）

**逻辑**：
- 买入：快速均线上穿慢速均线（金叉）
- 卖出：快速均线下穿慢速均线（死叉）

**参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| fast-period | 5 | 快速均线周期 |
| slow-period | 20 | 慢速均线周期 |

**适用场景**：
- 趋势明显的市场
- 中长期投资

### rsi（RSI 超买超卖）

**逻辑**：
- 买入：RSI 从上往下穿越超卖线（默认 30）
- 卖出：RSI 从下往上穿越超买线（默认 70）

**参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| rsi-period | 14 | RSI 计算周期 |
| rsi-upper | 70 | 超买阈值 |
| rsi-lower | 30 | 超卖阈值 |

**适用场景**：
- 震荡市场
- 短期波段操作

**示例**：

```bash
# 使用 RSI 策略回测
uv run --env-file .env python -m skills.backtest.scripts.backtest_processor.backtest_processor \
    --stock 000001 \
    --strategy rsi

# 自定义 RSI 参数
uv run --env-file .env python -m skills.backtest.scripts.backtest_processor.backtest_processor \
    --stock 000001 \
    --strategy rsi \
    --rsi-period 9 \
    --rsi-upper 80 \
    --rsi-lower 20
```

---

## 参数说明

### 必需参数

| 参数 | 说明 |
|------|------|
| --stock | 股票代码（如 000001） |

### 可选参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --strategy | ma_cross | 策略名称（ma_cross, rsi） |
| --start-date | 一年前 | 开始日期 |
| --end-date | 今天 | 结束日期 |
| --cash | 100000 | 初始资金 |
| --fast-period | 5 | 快速均线周期（ma_cross） |
| --slow-period | 20 | 慢速均线周期（ma_cross） |
| --rsi-period | 14 | RSI 计算周期（rsi） |
| --rsi-upper | 70 | RSI 超买阈值（rsi） |
| --rsi-lower | 30 | RSI 超卖阈值（rsi） |
| --quiet | false | 安静模式 |
| --output | 自动 | 输出文件路径 |

---

## 注意事项

### ⚠️ 风险提示

1. **历史表现不代表未来**：回测结果仅供参考，不构成投资建议
2. **策略过拟合**：过度优化参数可能导致策略在未来表现不佳
3. **市场环境变化**：策略在不同市场环境下表现可能差异较大

### 📊 A股特殊处理

| 问题 | 当前处理 | 未来优化 |
|------|---------|---------|
| 涨跌停 | 未处理 | 自定义 Broker |
| 交易费用 | 佣金 0.03%，印花税 0.1% | 精确计算 |
| 除权除息 | 前复权数据 | 支持后复权 |
| T+1 交易 | 未限制 | 策略中限制 |

---

## 参考资料

- [策略回测研究报告](../../research/backtest-research.md)
- [需求文档](../../docs/skills/backtest/spec.md)
