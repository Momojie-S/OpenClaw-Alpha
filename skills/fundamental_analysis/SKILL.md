---
name: openclaw_alpha_fundamental_analysis
description: "基本面分析，获取 PE/PB/ROE 等财务指标。适用于：(1) 单只股票基本面分析，(2) 了解公司财务健康度，(3) 评估投资价值。不适用于：港股/美股、深度财报分析、投资建议。"
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["uv"]
---

# 基本面分析

获取股票的财务指标（PE/PB/ROE等），评估公司基本面情况和投资价值。

## 使用说明

### 脚本运行

```bash
# 单只股票基本面分析
uv run --env-file .env python -m skills.fundamental_analysis.scripts.fundamental_processor.fundamental_processor --code 000001

# 包含估值历史数据
uv run --env-file .env python -m skills.fundamental_analysis.scripts.fundamental_processor.fundamental_processor --code 000001 --include-history
```

### 参数说明

| 参数 | 必填 | 说明 | 默认值 |
|------|:----:|------|--------|
| `--code` | 是 | 股票代码（6 位数字） | - |
| `--include-history` | 否 | 是否包含估值历史数据（近 30 天） | False |

### 输出示例

```json
{
  "code": "000001",
  "name": "平安银行",
  "report_date": "2025-09-30",
  "valuation": {
    "pe_ttm": 4.87,
    "pe_rating": "低估",
    "pb": 0.47,
    "pb_rating": "低估"
  },
  "profitability": {
    "roe": 8.28,
    "roe_rating": "一般",
    "eps": 1.87,
    "net_margin": null,
    "gross_margin": null
  },
  "growth": {
    "revenue_growth": -9.78,
    "profit_growth": -3.50,
    "growth_rating": "下滑"
  },
  "financial_health": {
    "debt_ratio": 91.01,
    "debt_rating": "正常",
    "current_ratio": null,
    "quick_ratio": null,
    "cash_per_share": 3.70
  },
  "summary": "估值偏低，ROE 一般，营收下滑"
}
```

## 分析步骤

### Step 1: 输入股票代码

**输入**：股票代码（如 `000001`）

**动作**：运行基本面分析脚本

```bash
uv run --env-file .env python -m skills.fundamental_analysis.scripts.fundamental_processor.fundamental_processor --code 000001
```

**输出**：基本面分析报告（JSON）

### Step 2: 查看估值指标

**关注点**：
- **PE**：市盈率（滚动 12 个月）
- **PB**：市净率
- **评级**：低估/合理/高估

**判断逻辑**：
| 指标 | 低估 | 合理 | 高估 |
|------|------|------|------|
| PE | < 15 | 15-25 | > 25 |
| PB | < 1.5 | 1.5-3 | > 3 |

### Step 3: 查看盈利能力

**关注点**：
- **ROE**：净资产收益率（最重要指标）
- **EPS**：每股收益
- **评级**：优秀/良好/一般/较差

**判断逻辑**：
| ROE | 评级 |
|-----|------|
| > 15% | 优秀 |
| 10-15% | 良好 |
| 5-10% | 一般 |
| < 5% | 较差 |

### Step 4: 查看成长性

**关注点**：
- **营收增长**：同比
- **利润增长**：同比
- **评级**：高增长/稳定增长/下滑

**判断逻辑**：
| 条件 | 评级 |
|------|------|
| 营收>20% 且 利润>20% | 高增长 |
| 营收>0 且 利润>0 | 稳定增长 |
| 营收<0 或 利润<0 | 下滑 |

### Step 5: 查看财务健康

**关注点**：
- **资产负债率**：负债/总资产
- **流动比率**：流动资产/流动负债
- **评级**：健康/正常/关注/风险

**判断逻辑**：
| 资产负债率 | 评级 |
|-----------|------|
| < 40% | 健康 |
| 40-60% | 正常 |
| 60-70% | 关注 |
| > 70% | 风险 |

**注**：金融行业（银行、保险）特殊处理，>90% 为正常。

## 评级体系

### 估值评级

| 指标 | 低估 | 合理 | 高估 |
|------|------|------|------|
| PE | < 15 | 15-25 | > 25 |
| PB | < 1.5 | 1.5-3 | > 3 |

### ROE 评级

| ROE | 评级 |
|-----|------|
| > 15% | 优秀 |
| 10-15% | 良好 |
| 5-10% | 一般 |
| < 5% | 较差 |

### 成长性评级

| 条件 | 评级 |
|------|------|
| 营收>20% 且 利润>20% | 高增长 |
| 营收>0 且 利润>0 | 稳定增长 |
| 营收<0 或 利润<0 | 下滑 |
| 营收<-10% 或 利润<-10% | 大幅下滑 |

### 资产负债率评级

| 资产负债率 | 评级 |
|-----------|------|
| < 40% | 健康 |
| 40-60% | 正常 |
| 60-70% | 关注 |
| > 70% | 风险 |

**注**：金融行业（银行、保险）>90% 为正常。

## 数据来源

- **财务指标**：AKShare - stock_financial_analysis_indicator_em（东方财富）
- **估值数据**：AKShare - stock_zh_valuation_baidu（百度股市通）

## 注意事项

1. **行业差异**：不同行业的估值标准不同（如银行 PE 低，科技股 PE 高）
2. **周期性**：周期性行业（如钢铁、煤炭）需看完整周期
3. **数据时效**：财务数据按季度更新，估值数据每日更新
4. **新股**：上市不足 1 年的股票可能缺少历史数据

## 参考资料

- [需求文档](../../docs/fundamental-analysis/spec.md)
- [设计文档](../../docs/fundamental-analysis/design.md)
