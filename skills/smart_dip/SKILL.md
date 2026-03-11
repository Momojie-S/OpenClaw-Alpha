---
name: openclaw_alpha_smart_dip
description: "智能定投策略：基于估值指标的定投金额建议。适用于：(1) 每月定投决策，(2) 估值驱动的仓位调整，(3) 定投历史分析。不适用于：个股选择、短期交易、择时买卖。"
metadata:
  openclaw:
    emoji: "💎"
    requires:
      bins: ["uv"]
---

# 智能定投策略

基于市场估值指标的智能定投方案，实现"低估值多投、高估值少投"。

## 使用说明

### 脚本运行

```bash
# 查看本月定投建议（股债性价比驱动）
uv run --env-file .env python -m openclaw_alpha.skills.smart_dip.dip_advice_processor.dip_advice_processor

# 指定基准金额
uv run --env-file .env python -m openclaw_alpha.skills.smart_dip.dip_advice_processor.dip_advice_processor --base-amount 2000

# 指定策略类型
uv run --env-file .env python -m openclaw_alpha.skills.smart_dip.dip_advice_processor.dip_advice_processor --strategy fed_model

# 查看定投历史
uv run --env-file .env python -m openclaw_alpha.skills.smart_dip.dip_history_processor.dip_history_processor --months 12
```

### 参数说明

**dip_advice_processor**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date` | 分析日期 | 今天 |
| `--base-amount` | 基准金额（元） | 1000 |
| `--strategy` | 策略：fed_model（股债性价比） | fed_model |

**dip_history_processor**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--months` | 回看月数 | 12 |
| `--base-amount` | 基准金额（元） | 1000 |

### 运行记录

输出文件保存在：`.openclaw_alpha/smart_dip/{日期}/dip_advice.json`

## 分析步骤

### Step 1: 获取本月定投建议

**输入**：基准金额（默认 1000 元）
**动作**：运行定投建议计算
**输出**：本期定投金额和倍数

```bash
uv run --env-file .env python -m openclaw_alpha.skills.smart_dip.dip_advice_processor.dip_advice_processor --base-amount 2000
```

**输出示例**：
```
=== 智能定投建议 ===
日期: 2026-03-08
基准金额: 2000 元

【估值分析】
股债性价比: 2.5%
市场状态: 低估

【定投建议】
倍数: 1.5x
建议金额: 3000 元
操作: 增加定投

【历史参考】
近3月平均倍数: 1.2x
近6月平均倍数: 1.3x
```

### Step 2: 查看定投历史

**输入**：回看月数
**动作**：运行定投历史分析
**输出**：历史定投倍数和累计金额

```bash
uv run --env-file .env python -m openclaw_alpha.skills.smart_dip.dip_history_processor.dip_history_processor --months 12
```

### Step 3: 制定定投计划

根据建议和历史分析，制定个人定投计划。

## 策略说明

### 股债性价比驱动（FED 模型）

**原理**：股债性价比 = 沪深300 E/P - 10Y 国债收益率

| 股债性价比 | 市场状态 | 定投倍数 | 操作建议 |
|------------|----------|----------|----------|
| > 3% | 极度低估 | 2.0x | 大幅加仓 |
| 2% - 3% | 低估 | 1.5x | 增加定投 |
| 0% - 2% | 合理 | 1.0x | 正常定投 |
| -1% - 0% | 高估 | 0.5x | 减半定投 |
| < -1% | 极度高估 | 0x | 暂停定投 |

### 优势

1. **降低平均成本**：低位多投，摊低成本
2. **纪律性强**：避免情绪化决策
3. **简单易懂**：基于单一指标，逻辑清晰
4. **数据现成**：股债性价比已有实现

### 风险提示

1. 估值指标有滞后性
2. 极端行情可能错过机会
3. 历史有效不代表未来有效
4. 不构成投资建议

## 注意事项

- 数据来源：Tushare（沪深300 PE、10Y 国债收益率）
- 适合长期投资（3 年以上）
- 建议结合个人风险承受能力调整
- 定投金额不超过月收入的 20%
