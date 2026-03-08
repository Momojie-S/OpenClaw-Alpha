---
name: openclaw_alpha_market_overview
description: "市场综合分析，一键生成完整市场报告。适用于：(1) 快速了解市场整体情况，(2) 生成每日市场简报，(3) 整合各层次分析结果。不适用于：个股选择、技术指标分析、实时推送。"
metadata:
  openclaw:
    emoji: "📋"
    requires:
      bins: ["uv"]
---

# 市场综合分析

一键式市场分析报告，整合宏观、情绪、板块、外资四个层次的分析结果。

## 使用说明

### 脚本运行

```bash
# 查看今日完整报告（默认）
uv run --env-file .env python skills/market_overview/scripts/overview_processor/overview_processor.py

# 一键生成（自动获取依赖数据）
uv run --env-file .env python skills/market_overview/scripts/overview_processor/overview_processor.py --auto-fetch

# 快速版（仅宏观+情绪）
uv run --env-file .env python skills/market_overview/scripts/overview_processor/overview_processor.py --mode quick

# 指定日期
uv run --env-file .env python skills/market_overview/scripts/overview_processor/overview_processor.py --date 2026-03-07

# JSON 输出
uv run --env-file .env python skills/market_overview/scripts/overview_processor/overview_processor.py --output json
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date` | 分析日期 | 今天 |
| `--mode` | quick(快速)/full(完整) | full |
| `--output` | text(Markdown)/json | text |
| `--auto-fetch` | 数据不存在时自动获取 | False |

### 运行记录

输出文件保存在：`.openclaw_alpha/market_overview/{日期}/report.json`

### 一键生成 vs 手动准备

**方式一：一键生成（推荐）**
```bash
uv run --env-file .env python skills/market_overview/scripts/overview_processor/overview_processor.py --auto-fetch
```
- 自动获取所有依赖数据
- 适合快速查看市场情况

**方式二：手动准备数据**
```bash
# 先运行依赖 skill
uv run --env-file .env python skills/index_analysis/scripts/index_processor/index_processor.py
uv run --env-file .env python skills/market_sentiment/scripts/sentiment_processor/sentiment_processor.py
# ///.py 其他 skill

# 再生成报告
uv run --env-file .env python skills/market_overview/scripts/overview_processor/overview_processor.py
```
- 适合需要精确控制数据获取的场景
- 可以单独更新某个 skill 的数据

### 依赖的 Skill

本 skill 需要以下 skill 的数据：
- `index_analysis` - 指数分析（必需）
- `market_sentiment` - 市场情绪（必需）
- `industry_trend` - 板块热度（完整版需要）
- `fund_flow_analysis` - 资金流向（完整版需要）
- `northbound_flow` - 北向资金（完整版需要）

使用 `--auto-fetch` 参数时，会自动调用这些 skill 获取数据。

## 分析步骤

### Step 1: 准备数据

**输入**：分析日期

**动作**：运行各个 skill 的 Processor 生成数据文件（推荐使用 `--auto-fetch` 自动获取）

```bash
# 宏观层数据
uv run --env-file .env python skills/index_analysis/scripts/index_processor/index_processor.py --date 2026-03-07

# 情绪数据
uv run --env-file .env python skills/market_sentiment/scripts/sentiment_processor/sentiment_processor.py --date 2026-03-07

# 板块数据（完整版需要）
uv run --env-file .env python skills/industry_trend/scripts/industry_trend_processor/industry_trend_processor.py --date 2026-03-07

# 资金流向（完整版需要）
uv run --env-file .env python skills/fund_flow_analysis/scripts/fund_flow_processor/fund_flow_processor.py --date 2026-03-07

# 外资数据（完整版需要）
uv run --env-file .env python skills/northbound_flow/scripts/northbound_processor/northbound_processor.py --action daily --date 2026-03-07
```

**输出**：各 skill 的 JSON 文件

### Step 2: 生成综合报告

**输入**：各 skill 的数据文件

**动作**：
```bash
uv run --env-file .env python skills/market_overview/scripts/overview_processor/overview_processor.py --date 2026-03-07
```

**输出**：
- 控制台：Markdown 格式的综合报告
- 文件：`.openclaw_alpha/market_overview/{date}/report.json`

### Step 3: 解读报告

报告包含五个部分：
1. **综合判断** - 整体市场判断（强势上涨/震荡上涨/震荡/震荡下跌/弱势下跌）
2. **市场概览** - 指数涨跌、市场温度
3. **情绪分析** - 涨跌停、资金流向、情绪评分
4. **板块热点** - 热门行业、概念、资金流向
5. **外资动向** - 北向资金、买入卖出 Top
6. **综合结论** - 总结、关注点、风险提示

## 综合判断规则

| 判断 | 条件 |
|------|------|
| 强势上涨 | 指数涨 > 1% + 情绪 > 60 + 外资流入 > 10 亿 |
| 震荡上涨 | 指数涨 0~1% + 情绪 > 40 |
| 震荡 | 涨跌互现 |
| 震荡下跌 | 指数跌 0~1% + 情绪 < 60 |
| 弱势下跌 | 指数跌 > 1% + 情绪 < 40 + 外资流出 > 10 亿 |

## 报告示例

```markdown
# 市场分析报告 - 2026-03-08

## 综合判断

**震荡上涨** (置信度: 70%)

## 一、市场概览

**市场温度**：正常
**整体趋势**：震荡

| 指数 | 收盘 | 涨跌幅 | 趋势 |
|------|------|--------|------|
| 上证指数 | 3345.67 | +0.50% | 震荡 |
| 创业板指 | 2256.78 | +1.20% | 震荡上涨 |

## 二、情绪分析

**情绪状态**：偏热 (温度: 65)

- 涨停：85 家
- 跌停：12 家
- 主力净流入：+25.3 亿

## 三、板块热点

**行业 Top 5**：
1. 电子 (+3.50%) - 加热中
2. 计算机 (+2.80%) - 加热中

**概念 Top 5**：
1. 人工智能 (+4.20%)
2. 机器人 (+3.80%)

## 四、外资动向

**北向资金**：流入 (+44.0 亿)

**买入 Top 5**：
- 贵州茅台 (+8.50 亿)
- 宁德时代 (+6.20 亿)

## 五、综合结论

指数震荡，情绪偏热，外资流入

**关注点**：
- 最强指数：创业板指 (+1.2%)
- 热门行业：电子 (+3.5%)
- 北向资金流入 44.0 亿
```

## 注意事项

1. **数据依赖**：需要先运行各 skill 生成数据文件
2. **容错设计**：部分数据缺失不影响整体报告生成
3. **数据一致性**：各 skill 的日期参数需保持一致
4. **快速版**：仅包含宏观和情绪，适合快速查看
5. **完整版**：包含全部四个层次，适合详细分析

## 使用建议

1. **日常使用**：快速版 + 个股分析
2. **周报/月报**：完整版 + 历史对比
3. **异常行情**：完整版 + 风险提示

## 深入分析

获取综合报告后，可以根据关注点深入分析：
- **指数** → [index_analysis](../index_analysis/SKILL.md)
- **情绪** → [market_sentiment](../market_sentiment/SKILL.md)
- **板块** → [industry_trend](../industry_trend/SKILL.md)
- **资金** → [fund_flow_analysis](../fund_flow_analysis/SKILL.md)
- **外资** → [northbound_flow](../northbound_flow/SKILL.md)
