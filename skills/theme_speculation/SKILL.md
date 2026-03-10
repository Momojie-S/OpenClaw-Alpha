---
name: openclaw_alpha_theme_speculation
description: "题材炒作分析：判断情绪周期、识别龙头股、提示炒作风险。适用于：(1) 分析题材股、概念股，(2) 追踪连板股、涨停板，(3) 判断题材炒作阶段，(4) 识别龙头/跟风/补涨股。不适用于：涨停预测、实时推送、涨停原因分析。"
metadata:
  openclaw:
    emoji: "🔥"
    requires:
      bins: ["uv"]
---

# 题材炒作分析

为题材炒作场景提供专用分析能力：情绪周期判断、龙头识别、炒作风险提示。

## 使用说明

### 脚本运行

```bash
# 情绪周期判断
uv run --env-file .env python -m openclaw_alpha.skills.theme_speculation.sentiment_cycle_processor.sentiment_cycle_processor

# 龙头识别
uv run --env-file .env python -m openclaw_alpha.skills.theme_speculation.dragon_head_processor.dragon_head_processor --board "人工智能"

# 炒作风险提示
uv run --env-file .env python -m openclaw_alpha.skills.theme_speculation.speculation_risk_processor.speculation_risk_processor --symbol "000001"
```

### 运行记录

运行记录保存在：
- 情绪周期：`.openclaw_alpha/theme_speculation/{date}/sentiment_cycle.json`
- 龙头识别：`.openclaw_alpha/theme_speculation/{date}/dragon_head.json`
- 风险提示：`.openclaw_alpha/theme_speculation/{date}/risk_{symbol}.json`

## 分析步骤

### Step 1: 判断情绪周期

**输入**：交易日期

**动作**：运行情绪周期 Processor
```bash
uv run --env-file .env python -m openclaw_alpha.skills.theme_speculation.sentiment_cycle_processor.sentiment_cycle_processor --date "2026-03-10"
```

**输出**：
- 情绪周期（启动/加速/高潮/分歧/退潮）
- 情绪指标（涨停家数、炸板率、连板高度、昨日涨停表现）
- 周期判断理由

---

### Step 2: 识别龙头股

**输入**：概念板块名称

**动作**：运行龙头识别 Processor
```bash
uv run --env-file .env python -m openclaw_alpha.skills.theme_speculation.dragon_head_processor.dragon_head_processor --board "人工智能"
```

**输出**：
- 龙头股（连板最高、封板最早）
- 跟风股列表
- 补涨股列表

---

### Step 3: 评估炒作风险

**输入**：股票代码

**动作**：运行风险提示 Processor
```bash
uv run --env-file .env python -m openclaw_alpha.skills.theme_speculation.speculation_risk_processor.speculation_risk_processor --symbol "000001"
```

**输出**：
- 情绪过热警示
- 炸板风险等级
- 监管风险提示
- 涨幅偏离提醒

---

## 参数说明

### sentiment_cycle_processor

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date` | 交易日期 (YYYY-MM-DD) | 今天 |

### dragon_head_processor

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--board` | 概念板块名称 | 必填 |
| `--date` | 交易日期 | 今天 |
| `--top-n` | 返回数量 | 10 |

### speculation_risk_processor

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--symbol` | 股票代码 | 必填 |
| `--date` | 交易日期 | 今天 |

---

## 情绪周期说明

| 周期 | 特征 | 操作建议 |
|------|------|----------|
| **启动** | 涨停数增加、炸板率低 | 可关注龙头 |
| **加速** | 涨停数持续增加 | 持仓待涨 |
| **高潮** | 涨停数最多 | 谨慎追高 |
| **分歧** | 涨停数减少、炸板率高 | 减仓观望 |
| **退潮** | 涨停数大幅减少 | 及时止损 |

---

## 龙头识别标准

| 类型 | 标准 |
|------|------|
| **龙头** | 连板最高、封板最早、市值较小 |
| **跟风** | 板块内跟涨、封板较晚（> 10:30） |
| **补涨** | 板块滞涨股、后发涨停 |

---

## 风险提示说明

| 风险类型 | 触发条件 |
|----------|----------|
| 情绪过热 | 涨停家数 > 100，连板高度 > 5 板 |
| 炸板风险高 | 炸板率 > 50% |
| 监管风险 | 连续 3 日涨停、短期涨幅 > 30% |
| 涨幅偏离 | PE 偏离行业均值 > 100% |

---

## 相关 Skill

| Skill | 联动方式 |
|-------|---------|
| limit_up_tracker | 提供涨停数据基础 |
| industry_trend | 提供板块数据 |
| risk_alert | 提供基本面风险 |

---

## 注意事项

1. **数据时效**：情绪周期基于当日收盘数据，盘中不更新
2. **龙头变化**：龙头股会随情绪周期变化而更替
3. **风险提示**：仅供参考，不构成投资建议
4. **涨停原因**：暂不支持（无免费 API）
