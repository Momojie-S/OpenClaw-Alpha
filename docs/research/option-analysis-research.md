# 期权分析研究

> 研究日期：2026-03-08
> 研究目的：探索期权分析能力，丰富投资分析框架

---

## 期权市场概述

期权是一种衍生性金融商品，赋予买方在特定时间以特定价格买卖标的物的权利。

**主要品种**：
- **ETF期权**：50ETF、300ETF、500ETF、科创50ETF、创业板ETF
- **股指期权**：沪深300（IO）、上证50（HO）、中证1000（MO）
- **商品期权**：铜、黄金、原油、豆粕等

---

## 期权的投资分析价值

### 1. 市场情绪指标

| 指标 | 说明 | 应用 |
|------|------|------|
| **PCR**（Put/Call Ratio） | 认沽/认购成交量或持仓量比 | PCR > 1 市场偏悲观，PCR < 0.7 市场偏乐观 |
| **隐含波动率** | 市场对未来波动的预期 | 波动率高时卖出期权，低时买入 |
| **成交量分布** | 认购vs认沽成交对比 | 判断资金方向 |

### 2. 风险管理

- **对冲工具**：买入认沽期权保护持仓
- **杠杆替代**：期权提供可控杠杆
- **收益增强**：卖出备兑认购期权增强收益

### 3. 策略应用

| 策略 | 适用场景 | 风险收益特征 |
|------|----------|-------------|
| 买入认购 | 看涨 | 有限风险，无限收益 |
| 买入认沽 | 看跌或对冲 | 有限风险，有限收益 |
| 卖出备兑认购 | 震荡或缓涨 | 增强收益，放弃上行空间 |
| 保护性认沽 | 持股避险 | 支付权利金，锁定下行风险 |

---

## AKShare 数据接口

### 核心接口

| 接口 | 功能 | 数据源 |
|------|------|--------|
| `option_finance_board` | 金融期权行情 | 上交所/深交所/中金所 |
| `option_risk_indicator_sse` | 期权风险指标 | 上交所 |
| `option_daily_stats_sse` | 上交所每日统计 | 上交所 |
| `option_daily_stats_szse` | 深交所每日统计 | 深交所 |

### 支持的期权品种

**ETF期权（上交所）**：
- 华夏上证50ETF期权（510050）
- 华泰柏瑞沪深300ETF期权（510300）
- 南方中证500ETF期权（510500）
- 华夏科创50ETF期权（588000）
- 易方达科创50ETF期权（588080）

**ETF期权（深交所）**：
- 嘉实沪深300ETF期权（159919）
- 嘉实中证500ETF期权（159922）
- 易方达创业板ETF期权（159915）
- 易方达深证100ETF（159901）

**股指期权（中金所）**：
- 沪深300股指期权（IO）
- 上证50股指期权（HO）
- 中证1000股指期权（MO）

### 关键数据字段

**期权风险指标**（`option_risk_indicator_sse`）：
- `DELTA_VALUE` - Delta值（标的价格敏感度）
- `GAMMA_VALUE` - Gamma值（Delta变化率）
- `VEGA_VALUE` - Vega值（波动率敏感度）
- `THETA_VALUE` - Theta值（时间衰减）
- `RHO_VALUE` - Rho值（利率敏感度）
- `IMPLC_VOLATLTY` - 隐含波动率

**每日统计**（`option_daily_stats_sse/szse`）：
- `认购成交量` / `认沽成交量`
- `认沽/认购`（PCR）
- `未平仓认购合约数` / `未平仓认沽合约数`

---

## Skill 设计方案

### skill 名称
`option_analysis`（期权分析）

### 核心功能

| Processor | 功能 | 输出 |
|-----------|------|------|
| `sentiment_processor` | 期权情绪分析 | PCR、波动率、成交分布 |
| `market_overview_processor` | 期权市场概况 | 各品种成交/持仓统计 |

### 情绪分析指标

**PCR 指标解读**：
```
PCR > 1.2  → 极度悲观，可能反转向上
PCR 0.8-1.2 → 中性
PCR < 0.7  → 极度乐观，可能反转向下
```

**隐含波动率解读**：
```
IV > 30%  → 市场恐慌，可能见底
IV 15-30% → 正常波动
IV < 15%  → 市场平静，可能变盘
```

### 使用示例

```bash
# 获取期权情绪分析
uv run --env-file .env python -m skills.option_analysis.scripts.sentiment_processor.sentiment_processor \
    --underlying 510050 \
    --date 2026-03-08

# 输出示例：
# {
#   "underlying": "50ETF",
#   "date": "2026-03-08",
#   "pcr_volume": 0.85,
#   "pcr_sentiment": "偏乐观",
#   "iv_atm": 18.5,
#   "iv_level": "正常",
#   "call_volume": 150000,
#   "put_volume": 127500,
#   "signal": "市场情绪偏乐观，需警惕回调风险"
# }
```

---

## 开发优先级

### P1 - 核心功能（推荐优先开发）

| 功能 | 难度 | 价值 |
|------|------|------|
| 期权情绪分析（PCR + IV） | 低 | 高 |
| 期权市场概况 | 低 | 中 |

### P2 - 扩展功能

| 功能 | 难度 | 价值 |
|------|------|------|
| 期权Greeks分析 | 中 | 中 |
| 期权策略建议 | 高 | 高 |

---

## 与现有框架的整合

### 层次定位

期权分析属于**宏观层**，提供市场情绪判断：

```
宏观层
├── index_analysis（指数分析）
├── market_sentiment（市场情绪）
├── margin_trading（融资融券）
└── option_analysis（期权分析）← 新增
```

### 分析流程

1. **宏观判断** → index_analysis + option_analysis（期权情绪）
2. **中观选择** → industry_trend（行业热度）
3. **微观选股** → stock_screener
4. **组合管理** → portfolio_analysis

---

## 参考资料

- [AKShare 期权数据文档](https://akshare.akfamily.xyz/data/option/option.html)
- [期权定价理论 - Black-Scholes 模型](https://zh.wikipedia.org/wiki/期权)
- [VIX 恐慌指数](https://zh.wikipedia.org/wiki/VIX指数)
