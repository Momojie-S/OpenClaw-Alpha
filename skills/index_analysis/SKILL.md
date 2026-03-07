---
name: openclaw_alpha_index_analysis
description: "指数分析，提供主要指数（上证、深证、创业板、科创50、沪深300、中证500）的行情数据和技术分析。适用于：(1) 了解大盘整体走势，(2) 判断市场趋势和转折点，(3) 分析指数强弱对比。不适用于：分时图分析、高级技术指标、指数成份股分析。"
metadata:
  openclaw:
    emoji: "📈"
    requires:
      bins: ["uv"]
---

# 指数分析

提供主要指数的行情数据和技术分析，帮助了解大盘整体走势。

## 使用说明

### 脚本运行

```bash
# 查看今日指数分析
uv run --env-file .env python -m skills.index_analysis.scripts.index_processor.index_processor

# 指定日期
uv run --env-file .env python -m skills.index_analysis.scripts.index_processor.index_processor --date 2026-03-06

# 只看部分指数
uv run --env-file .env python -m skills.index_analysis.scripts.index_processor.index_processor --top-n 3
```

### 运行记录

所有运行记录保存在 `{workspace}/.openclaw_alpha/index_analysis/{YYYY-MM-DD}/` 目录。

## 分析步骤

### Step 1: 获取指数行情

**输入**：分析日期

**动作**：
```bash
uv run --env-file .env python -m skills.index_analysis.scripts.index_processor.index_processor --date 2026-03-06
```

**输出**：
- 控制台：精简的指数分析结果
- 文件：完整数据（`.openclaw_alpha/index_analysis/{date}/index.json`）

**结果示例**：
```json
{
  "date": "2026-03-06",
  "market_temperature": "正常",
  "overall_trend": "震荡",
  "strongest": {"name": "创业板指", "change_pct": 1.5},
  "weakest": {"name": "上证指数", "change_pct": -0.3},
  "indices": [
    {
      "name": "上证指数",
      "code": "sh000001",
      "close": 3345.67,
      "change_pct": -0.3,
      "ma5": 3352.1,
      "ma20": 3310.5,
      "trend": "震荡"
    }
  ]
}
```

### Step 2: 结合其他 Skill 深入分析

根据指数分析结果，可以：

1. **市场温度过热/过冷** → 查看 [market_sentiment](../market_sentiment/SKILL.md) 了解情绪细节
2. **指数下跌但板块分化** → 查看 [industry_trend](../industry_trend/SKILL.md) 找抗跌板块
3. **指数上涨** → 用 [stock_screener](../stock_screener/SKILL.md) 筛选强势股

## 趋势判断说明

| 趋势 | 判断规则 |
|------|----------|
| 强势上涨 | 价格 > MA5 > MA20 且 涨幅 > 1% |
| 震荡上涨 | MA5 > MA20 且 涨幅 0~1% |
| 震荡 | MA5 与 MA20 接近，涨跌幅 < 1% |
| 震荡下跌 | MA5 < MA20 且 跌幅 0~1% |
| 弱势下跌 | 价格 < MA5 < MA20 且 跌幅 > 1% |

## 市场温度说明

| 温度 | 条件 |
|------|------|
| 过热 | 3个以上指数涨幅 > 2% |
| 温热 | 2个指数涨幅 > 1% |
| 正常 | 涨跌互现 |
| 偏冷 | 2个指数跌幅 > 1% |
| 过冷 | 3个以上指数跌幅 > 2% |
