---
name: openclaw_alpha_portfolio_analysis
description: "持仓分析，帮助用户分析投资组合的结构、风险敞口和分散程度。适用于：(1) 分析持仓权重分布，(2) 了解行业集中度，(3) 检查风险提示。不适用于：历史持仓追踪、调仓建议。"
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["uv"]
---

# 持仓分析

帮助用户快速了解投资组合的整体状况，包括持仓结构、行业分布、集中度风险。

## 使用说明

### 脚本运行

所有脚本需在项目根目录下运行，使用 `uv run --env-file .env` 加载环境变量：

```bash
uv run --env-file .env python -m skills.portfolio_analysis.scripts.portfolio_processor [参数]
```

**如果脚本运行失败**：
1. 检查是否在项目根目录
2. 检查网络连接（需要访问东方财富接口）
3. 将错误信息记录到进度文件，不要丢失上下文

### 运行记录

**进度文件位置**：`.openclaw_alpha/portfolio-analysis/{YYYY-MM-DD}/progress.md`

每次运行脚本后，记录：
- 运行时间
- 脚本命令
- 运行结果（成功/失败）
- 关键输出（总市值、风险提示）
- 错误信息（如有）

## 分析步骤

### Step 1: 使用持仓字符串分析

**输入**：持仓字符串（代码:股数[:成本价]）

**动作**：
```bash
# 简单模式（无成本价）
uv run --env-file .env python -m skills.portfolio_analysis.scripts.portfolio_processor \
    --holdings "000001:1000,600000:500,002475:200"

# 完整模式（含成本价，可计算盈亏）
uv run --env-file .env python -m skills.portfolio_analysis.scripts.portfolio_processor \
    --holdings "000001:1000:12.5,600000:500:8.2,002475:200:25.0"
```

**输出**：
- 控制台：持仓摘要 + 风险提示
- 文件：`.openclaw_alpha/portfolio-analysis/{date}/portfolio.json`

**分析要点**：
- 关注 `总市值`：当前持仓总价值
- 查看 `集中度`：HHI 指数判断分散程度
- 检查 `风险提示`：是否有集中度过高的问题

### Step 2: 使用 JSON 文件分析

**输入**：JSON 文件路径

**文件格式**：
```json
{
  "holdings": [
    {"code": "000001", "shares": 1000, "cost": 12.5},
    {"code": "600000", "shares": 500, "cost": 8.2},
    {"code": "002475", "shares": 200}
  ]
}
```

**动作**：
```bash
uv run --env-file .env python -m skills.portfolio_analysis.scripts.portfolio_processor \
    --file portfolio.json
```

**输出**：同 Step 1

## 分析指标

### 集中度指标 (HHI)

| HHI 范围 | 状态 | 说明 |
|---------|------|------|
| < 1500 | 分散 | 持仓分散，风险较低 |
| 1500-2500 | 中等 | 适度分散 |
| > 2500 | 高度集中 | 持仓集中，风险较高 |

### 风险提示

| 风险类型 | 触发条件 | 级别 |
|---------|---------|------|
| 单股集中 | 单股权重 > 30% | 高 ⚠️ |
| 行业集中 | 单行业权重 > 50% | 高 ⚠️ |
| 持仓过少 | 股票数 < 3 | 中 ⚡ |
| 持仓过多 | 股票数 > 20 | 低 ℹ️ |

## 输出示例

```
持仓分析报告
========================================
总市值：¥125,680.00
总盈亏：+¥8,320.00 (+7.1%)
集中度：中等 (HHI: 1823.45)

持仓分布（按市值）：
1. 平安银行(000001) - 35.2% - ¥44,200 - +¥2,100 (+5.0%)
2. 浦发银行(600000) - 25.1% - ¥31,550 - +¥410 (+1.3%)
3. 立讯精密(002475) - 15.8% - ¥19,850 - +¥5,810 (+41.3%)

行业分布：
- 银行：60.3% (2只)
- 电子：15.8% (1只)

风险提示：
⚠️ 单股集中度过高: 平安银行(000001): 权重 35.2% 超过 30% 阈值
```

## 后续分析

如需更深入的分析，可以：
1. 使用 `risk_alert` skill 分析各持仓的风险信号
2. 使用 `stock_analysis` skill 查看个股详细分析
3. 使用 `industry_trend` skill 分析行业热度
