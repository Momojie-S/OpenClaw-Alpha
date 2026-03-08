---
name: openclaw_alpha_risk_alert
description: "股票风险监控。适用于：(1) 检查个股风险信号（业绩、价格、资金），(2) 批量扫描多只股票风险，(3) 识别业绩暴雷风险，(4) 监控连续下跌和资金流出。不适用于：实时风险预警、量化风险模型、组合风险管理。"
metadata:
  openclaw:
    emoji: "⚠️"
    requires:
      bins: ["uv"]
---

# 风险监控 Skill

帮助投资者识别股票风险信号，包括业绩风险、价格风险、资金风险。支持单股检查和批量扫描。

## 使用说明

### 脚本运行

```bash
# 检查个股风险
uv run --env-file .env python skills/risk_alert/scripts/risk_processor/risk_processor.py <股票代码> [--date YYYY-MM-DD] [--days N]

# 批量检查（逗号分隔）
uv run --env-file .env python skills/risk_alert/scripts/risk_processor/risk_processor.py --batch "000001,600000,002475"

# 从文件读取
uv run --env-file .env python skills/risk_alert/scripts/risk_processor/risk_processor.py --batch-file stocks.txt

# 检查自选股风险
uv run --env-file .env python skills/risk_alert/scripts/risk_processor/risk_processor.py --watchlist

# 指定日期和天数
uv run --env-file .env python skills/risk_alert/scripts/risk_processor/risk_processor.py --batch "000001,600000" --date 2026-03-07 --days 5

# 保存结果
uv run --env-file .env python skills/risk_alert/scripts/risk_processor/risk_processor.py --watchlist --output
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `symbol` | 股票代码（单股检查） | - |
| `--date` | 检查日期 | 今天 |
| `--days` | 检查近 N 天 | 5 |
| `--batch` | 批量检查（逗号分隔） | - |
| `--batch-file` | 从文件读取股票列表 | - |
| `--watchlist` | 从自选股列表读取 | False |
| `--output` | 保存结果到文件 | False |
| `--top-n` | 每个风险等级显示数量 | 10 |

### 运行记录

运行记录保存在 `.openclaw_alpha/risk_alert/YYYY-MM-DD/` 目录下：
- 单股检查：`risk_check.json`
- 批量扫描：`batch_risk_scan.json`

## 分析步骤

### Step 1a: 单股风险检查

**输入**：6位股票代码

**动作**：运行风险检查脚本

```bash
uv run --env-file .env python skills/risk_alert/scripts/risk_processor/risk_processor.py 000001
```

**输出**：风险检查结果

```json
{
  "code": "002364",
  "name": "中恒电气",
  "date": "2026-03-07",
  "rating": "高",
  "risks": [
    {
      "type": "业绩风险",
      "level": "高",
      "detail": "业绩首亏，预计变动 -336.7%"
    }
  ],
  "suggestions": [
    "关注业绩公告详情",
    "评估业绩对股价的潜在影响"
  ]
}
```

### Step 1b: 批量风险扫描

**输入**：股票列表（命令行/文件/自选股）

**动作**：运行批量风险扫描

```bash
# 方式 1：直接指定股票
uv run --env-file .env python skills/risk_alert/scripts/risk_processor/risk_processor.py --batch "000001,600000,002475"

# 方式 2：从文件读取
uv run --env-file .env python skills/risk_alert/scripts/risk_processor/risk_processor.py --batch-file stocks.txt

# 方式 3：检查自选股
uv run --env-file .env python skills/risk_alert/scripts/risk_processor/risk_processor.py --watchlist
```

**输出**：批量风险扫描报告

```
============================================================
风险扫描报告 - 2026-03-08
============================================================

检查股票: 10 只

【汇总统计】
  高风险: 1 只
  中风险: 2 只
  低风险: 3 只
  正常: 4 只

【高风险】(1 只)
  002364 中恒电气: 业绩首亏，预计变动 -336.7%

【中风险】(2 只)
  600000 浦发银行: 连续下跌 3 天，累计跌幅 12.5%
  002475 立讯精密: 连续 3 天主力净流出，累计 2.3 亿

【低风险】(3 只)
  ///.py

【正常】(4 只)
  000001 平安银行: 无明显风险
  ///.py
```

### Step 2: 查看风险详情

**输入**：Step 1 的输出

**动作**：分析风险类型和建议

**输出**：风险分析结论

| 风险类型 | 高风险信号 | 中风险信号 |
|---------|-----------|-----------|
| 业绩风险 | 首亏、预减、增亏、续亏 | 不确定、略减 |
| 价格风险 | 单日跌幅 ≥9% | 连续下跌 ≥3 天且累计跌幅 ≥10% |
| 资金风险 | 单日主力净流出 ≥5 亿 | 连续 ≥3 天净流出且累计 ≥1 亿 |

### Step 3: 综合评估

**输入**：风险详情 + 持仓信息

**动作**：结合持仓比例、风险承受能力综合评估

**输出**：投资决策建议

**建议参考**：
- **高风险**：考虑减仓或规避
- **中风险**：密切关注，谨慎操作
- **低风险**：关注但不紧张
- **正常**：无明显风险信号

## 风险等级说明

### 综合评级规则

- **高风险**：存在 ≥1 个高风险信号
- **中风险**：存在 ≥1 个中风险信号，无高风险
- **低风险**：存在 ≥1 个低风险信号，无中高风险
- **正常**：无任何风险信号

### 风险类型详解

#### 业绩风险

基于业绩预告数据判断：

| 预告类型 | 风险等级 |
|---------|---------|
| 首亏、预减、增亏、续亏 | 高 |
| 不确定、略减 | 中 |
| 预增、略增、扭亏、减亏、续盈 | 无 |

#### 价格风险

基于近 N 日日线数据判断：

| 规则 | 条件 | 风险等级 |
|------|------|---------|
| 大幅下跌 | 单日跌幅 ≥9% | 高 |
| 连续下跌 | 连续 ≥3 天且累计跌幅 ≥10% | 中 |

#### 资金风险

基于近 N 日资金流向数据判断：

| 规则 | 条件 | 风险等级 |
|------|------|---------|
| 大额流出 | 单日主力净流出 ≥5 亿 | 高 |
| 持续流出 | 连续 ≥3 天且累计流出 ≥1 亿 | 中 |

## 注意事项

1. **数据延迟**：业绩预告数据可能不是最新的，请以公告为准
2. **网络不稳定**：部分 AKShare 接口（东方财富）网络不稳定，可能需要重试
3. **停牌股票**：停牌股票可能无法获取最新数据
4. **批量检查耗时**：批量检查多只股票可能需要较长时间
5. **仅供参考**：风险提示仅供参考，不构成投资建议

## 已实现功能

- ✅ 业绩风险检查（业绩预告）
- ✅ 价格风险检查（连续下跌）
- ✅ 资金风险检查（持续流出）
- ✅ 综合评级和建议
- ✅ 批量风险扫描（命令行/文件/自选股）

## 待实现功能

- 大股东减持监控
- 股权质押风险
- 风险趋势分析
