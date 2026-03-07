---
name: openclaw_alpha_option_analysis
description: "期权市场情绪分析。适用于：(1) 判断市场多空情绪（PCR + 隐含波动率），(2) 监控期权市场成交/持仓概况。不适用于：期权定价、复杂策略组合。"
metadata:
  openclaw:
    emoji: "📈"
    requires:
      bins: ["uv"]
---

# 期权分析

通过期权市场数据判断投资者情绪，辅助宏观层分析。

---

## 使用说明

### 脚本运行

```bash
# 情绪分析（PCR + IV）
uv run --env-file .env python -m skills.option_analysis.scripts.sentiment_processor.sentiment_processor \
    --underlying 510050 \
    --date 2026-03-08

# 市场概况（各品种统计）
uv run --env-file .env python -m skills.option_analysis.scripts.market_overview_processor.market_overview_processor \
    --date 2026-03-08
```

### 运行记录

数据保存在 `.openclaw_alpha/option_analysis/{YYYY-MM-DD}/` 目录下。

---

## 分析步骤

### Step 1: 情绪分析

**输入**：标的代码（如 510050 50ETF）

**动作**：
```bash
uv run --env-file .env python -m skills.option_analysis.scripts.sentiment_processor.sentiment_processor \
    --underlying 510050
```

**输出**：
```json
{
  "underlying": "50ETF",
  "date": "2026-03-08",
  "pcr_volume": 0.85,
  "pcr_oi": 0.92,
  "sentiment": "偏乐观",
  "iv_atm": 18.5,
  "iv_level": "正常",
  "call_volume": 150000,
  "put_volume": 127500,
  "signal": "市场情绪偏乐观，需警惕回调风险"
}
```

**指标解读**：

| PCR 范围 | 情绪判断 | 含义 |
|----------|----------|------|
| > 1.2 | 极度悲观 | 市场过度恐慌，可能反转向上 |
| 0.8-1.2 | 中性 | 多空平衡 |
| < 0.7 | 极度乐观 | 市场过度亢奋，可能反转向下 |

| IV 范围 | 波动判断 | 含义 |
|---------|----------|------|
| > 30% | 高波动 | 市场恐慌，可能见底 |
| 15-30% | 正常 | 市场平稳运行 |
| < 15% | 低波动 | 市场平静，可能变盘 |

### Step 2: 市场概况

**输入**：日期（可选，默认今天）

**动作**：
```bash
uv run --env-file .env python -m skills.option_analysis.scripts.market_overview_processor.market_overview_processor
```

**输出**：
```json
{
  "date": "2026-03-08",
  "total_volume": 2500000,
  "total_oi": 5200000,
  "etf_options": [
    {"name": "50ETF", "volume": 500000, "oi": 1200000, "pcr": 0.85},
    {"name": "300ETF", "volume": 450000, "oi": 1100000, "pcr": 0.92}
  ],
  "index_options": [
    {"name": "沪深300(IO)", "volume": 300000, "oi": 800000, "pcr": 1.05}
  ]
}
```

---

## 支持的标的

### ETF期权（上交所）
- 510050 - 华夏上证50ETF
- 510300 - 华泰柏瑞沪深300ETF
- 510500 - 南方中证500ETF
- 588000 - 华夏科创50ETF
- 588080 - 易方达科创50ETF

### ETF期权（深交所）
- 159919 - 嘉实沪深300ETF
- 159922 - 嘉实中证500ETF
- 159915 - 易方达创业板ETF

### 股指期权（中金所）
- IO - 沪深300股指期权
- HO - 上证50股指期权
- MO - 中证1000股指期权

---

## 与其他 Skill 配合

```
宏观层
├── index_analysis（指数走势）
├── market_sentiment（涨跌停/资金）
├── margin_trading（融资融券）
└── option_analysis（期权情绪）← 本 Skill
```

**典型流程**：
1. index_analysis 看指数趋势
2. option_analysis 看期权情绪（PCR + IV）
3. market_sentiment 看市场温度
4. 综合判断宏观环境

---

## 注意事项

- PCR 是反向指标：极端悲观可能是买入机会
- IV 高位时市场可能见底，低位时可能变盘
- 期权数据反映的是期权市场参与者情绪，与现货市场可能有差异
