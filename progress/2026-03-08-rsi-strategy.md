# 任务：添加 RSI 策略到回测系统

## 需求

为 backtest skill 添加 RSI（相对强弱指标）超买超卖策略，丰富策略库。

**分析思路**：
- RSI 是经典技术指标，适合震荡市场
- 利用 Backtrader 内置 RSI 指标
- 逻辑：RSI < 30 买入，RSI > 70 卖出

## Phase 1: 研究
- [x] 确认 Backtrader RSI 指标用法
- [x] 设计策略参数

## Phase 2: 开发
- [x] 实现 rsi_strategy.py
- [x] 更新 backtest_processor 支持策略选择
- [x] 更新 SKILL.md 文档

## Phase 3: 验证
- [x] 语法检查 - 通过

## Phase 4: 提交
- [x] git commit
- [x] git push

## 状态
- **当前阶段**：✅ 已完成
- **进度**：正常
- **完成时间**：2026-03-08 08:55

## 完成总结

### 新增功能

**RSI 超买超卖策略** - `rsi_strategy.py`

**功能**：
1. RSI 指标计算（默认 14 日）
2. 超买超卖信号检测
3. 可自定义参数（周期、阈值）

**策略逻辑**：
- 买入：RSI 从上往下穿越超卖线（默认 30）
- 卖出：RSI 从下往上穿越超买线（默认 70）

**命令**：
```bash
# 使用默认参数
uv run --env-file .env python -m skills.backtest.scripts.backtest_processor.backtest_processor \
    --stock 000001 \
    --strategy rsi

# 自定义参数
uv run --env-file .env python -m skills.backtest.scripts.backtest_processor.backtest_processor \
    --stock 000001 \
    --strategy rsi \
    --rsi-period 9 \
    --rsi-upper 80 \
    --rsi-lower 20
```

### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| rsi-period | 14 | RSI 计算周期 |
| rsi-upper | 70 | 超买阈值 |
| rsi-lower | 30 | 超卖阈值 |

### 适用场景

- 震荡市场
- 短期波段操作

### 提交记录

- 02e0b93 feat: 添加 RSI 超买超卖策略到回测系统

## 备注
开始时间：2026-03-08 08:45
完成时间：2026-03-08 08:55
耗时：10 分钟
