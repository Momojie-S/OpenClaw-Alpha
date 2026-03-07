---
name: openclaw_alpha_northbound_flow
description: "北向资金追踪，监控外资动向。适用于：(1) 查看当日外资净流入情况，(2) 了解外资买入/卖出的个股，(3) 分析外资近期流向趋势。不适用于：内资流向、行业资金分布。"
metadata:
  openclaw:
    emoji: "🌏"
    requires:
      bins: ["uv"]
---

# 北向资金追踪

追踪外资通过沪深港通流入 A 股的情况，作为投资决策参考。

## 使用说明

### 脚本运行

所有脚本需在项目根目录下运行，使用 `uv run --env-file .env` 加载环境变量：

```bash
uv run --env-file .env python -m skills.northbound_flow.scripts.northbound_processor.northbound_processor [参数]
```

**如果脚本运行失败**：
1. 检查是否在项目根目录
2. 检查网络连接（需要访问东方财富接口）
3. 将错误信息记录到进度文件，不要丢失上下文

### 运行记录

**进度文件位置**：`.openclaw_alpha/northbound-flow/{YYYY-MM-DD}/progress.md`

每次运行脚本后，记录：
- 运行时间
- 脚本命令
- 运行结果（成功/失败）
- 关键输出（净流入金额、Top 3 股票）
- 错误信息（如有）

## 分析步骤

### Step 1: 查看每日净流入

**输入**：日期（默认今天）

**动作**：
```bash
uv run --env-file .env python -m skills.northbound_flow.scripts.northbound_processor.northbound_processor \
    --action daily
```

**输出**：
- 控制台：当日净流入摘要 + Top 3 流入/流出股票
- 文件：`.openclaw_alpha/northbound-flow/{date}/northbound.json`（完整数据）

**分析要点**：
- 关注 `total_flow`：合计净流入金额
- 查看 `status`：大幅流入/流入/平衡/流出/大幅流出
- 结合 `top_inflow` 和 `top_outflow`：外资在买什么、卖什么

### Step 2: 查看个股流向详情

**输入**：日期（默认今天）、Top N（默认 10）

**动作**：
```bash
uv run --env-file .env python -m skills.northbound_flow.scripts.northbound_processor.northbound_processor \
    --action stock \
    --top-n 20
```

**输出**：
- 控制台：Top N 流入/流出股票
- 文件：`.openclaw_alpha/northbound-flow/{date}/northbound_stock.json`

**分析要点**：
- 关注 `hold_change`：持仓变化金额
- 查看 `hold_ratio`：持股比例变化
- 结合个股分析：外资买的是不是龙头？

### Step 3: 查看资金趋势

**输入**：天数（默认 5）、结束日期（默认今天）

**动作**：
```bash
uv run --env-file .env python -m skills.northbound_flow.scripts.northbound_processor.northbound_processor \
    --action trend \
    --days 10
```

**输出**：
- 控制台：资金趋势摘要
- 文件：`.openclaw_alpha/northbound-flow/{date}/northbound_trend_10d.json`

**分析要点**：
- 关注 `trend`：持续流入/持续流出/震荡
- 查看 `total_inflow`：累计净流入
- 结合 `inflow_days` 和 `outflow_days`：流入流出天数比

## 输出说明

### 每日净流入（daily）

```json
{
  "date": "2026-03-07",
  "total_flow": 44.0,
  "status": "流入",
  "sh_flow": 25.3,
  "sz_flow": 18.7,
  "top_inflow": [
    {"name": "贵州茅台", "hold_change": 85000},
    {"name": "宁德时代", "hold_change": 62000},
    {"name": "比亚迪", "hold_change": 48000}
  ],
  "top_outflow": [
    {"name": "中国平安", "hold_change": -32000},
    {"name": "招商银行", "hold_change": -28000}
  ]
}
```

### 个股流向（stock）

```json
{
  "date": "2026-03-07",
  "top_inflow": [
    {
      "code": "600519",
      "name": "贵州茅台",
      "hold_change": 85000,
      "hold_ratio": 0.05,
      "direction": "流入"
    },
    ...
  ],
  "top_outflow": [...]
}
```

### 资金趋势（trend）

```json
{
  "period": 5,
  "total_inflow": 120.5,
  "avg_inflow": 24.1,
  "inflow_days": 3,
  "outflow_days": 2,
  "trend": "持续流入",
  "summary": "近 5 天北向资金累计流入 120.5 亿元"
}
```

## 资金状态判断

| 净流入范围 | 状态 | 市场含义 |
|------------|------|----------|
| > 50 亿 | 大幅流入 | 外资看好，积极买入 |
| 10 ~ 50 亿 | 流入 | 外资稳步加仓 |
| -10 ~ 10 亿 | 平衡 | 外资观望 |
| -50 ~ -10 亿 | 流出 | 外资减仓 |
| < -50 亿 | 大幅流出 | 外资撤离，注意风险 |

## 趋势判断

| 条件 | 趋势 |
|------|------|
| 净流入天数 >= 总天数 * 70% | 持续流入 |
| 净流出天数 >= 总天数 * 70% | 持续流出 |
| 其他 | 震荡 |

## 数据源

- **每日净流入**：AKShare（免费）
- **个股持股**：AKShare（免费）
- 数据来源：东方财富

## 注意事项

1. **数据延迟**：盘中数据有 15 分钟延迟
2. **非交易日**：返回最近交易日的数据
3. **单位说明**：
   - 净流入：亿元
   - 个股持仓变化：万元

## 使用建议

1. **结合市场情绪**：外资流入 + 市场情绪好 = 可能持续上涨
2. **关注持续性**：持续流入的股票值得重点关注
3. **不要盲目跟风**：外资也会犯错，需要结合其他分析

## 深入分析

获取北向资金数据后，可以使用其他 skill 进行深入分析：
- **stock_analysis**：分析外资买入个股的行情
- **industry_trend**：查看外资买入股票所在板块的热度
- **market_sentiment**：了解整体市场情绪
