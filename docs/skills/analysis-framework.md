# 投资分析框架

> 本文档定义 OpenClaw-Alpha 的分析体系，指导 skill 开发方向。

---

## 分析层次

| 层次 | 核心问题 | 已有 Skill | 待补充 |
|------|----------|-----------|--------|
| **宏观** | 市场整体如何？ | index_analysis, market_sentiment | - |
| **中观** | 哪些板块热门？ | industry_trend, northbound_flow, lhb_tracker | - |
| **微观** | 买什么股票？ | stock_analysis, stock_screener, risk_alert | 基本面分析 |
| **事件** | 有什么新闻/事件？ | news_driven_investment, limit_up_tracker | 公告解读 |
| **组合** | 我的持仓怎么样？ | portfolio_analysis, watchlist_monitor | 盈亏追踪 |

---

## Skill 定位

### 宏观层

| Skill | 定位 | 数据源 |
|-------|------|--------|
| **index_analysis** | 6 大核心指数分析，判断大盘趋势 | Tushare |
| **market_sentiment** | 涨跌停、资金流向，评估市场温度 | AKShare |

### 中观层

| Skill | 定位 | 数据源 |
|-------|------|--------|
| **industry_trend** | 产业/概念板块热度追踪 | AKShare |
| **northbound_flow** | 外资动向监控 | AKShare |
| **lhb_tracker** | 游资/机构动向（龙虎榜） | AKShare |

### 微观层

| Skill | 定位 | 数据源 |
|-------|------|--------|
| **stock_analysis** | 单只股票行情快照 | AKShare |
| **stock_screener** | 多条件选股筛选 | AKShare |
| **risk_alert** | 个股风险监控（业绩/价格/资金） | AKShare |

### 事件层

| Skill | 定位 | 数据源 |
|-------|------|--------|
| **news_driven_investment** | 新闻驱动投资分析 | AKShare |
| **limit_up_tracker** | 涨停板追踪（连板/炸板） | AKShare |

### 组合层

| Skill | 定位 | 数据源 |
|-------|------|--------|
| **portfolio_analysis** | 持仓结构分析 | 本地数据 |
| **watchlist_monitor** | 自选股监控 | AKShare |

---

## 层次关联

```
宏观层（判断大势）
    ↓
中观层（找方向）
    ↓
微观层（选标的）
    ↓
事件层（找催化）
    ↓
组合层（管持仓）
```

**典型流程**：
1. **宏观** - index_analysis 看指数，market_sentiment 看情绪
2. **中观** - industry_trend 找热门板块，northbound_flow 看外资偏好
3. **微观** - stock_screener 筛选个股，risk_alert 检查风险
4. **事件** - news_driven_investment 找催化，limit_up_tracker 追踪热点
5. **组合** - portfolio_analysis 管理持仓，watchlist_monitor 跟踪关注

---

## 待补充能力

### P0 - 核心缺失

| 能力 | 说明 | 难点 |
|------|------|------|
| 基本面分析 | PE/PB/ROE/财报 | 数据源选择 |
| 盈亏追踪 | 持仓盈亏计算 | 交易记录管理 |

### P1 - 体验提升

| 能力 | 说明 | 难点 |
|------|------|------|
| 公告解读 | 上市公司公告分析 | NLP 处理 |
| 技术指标 | MACD/KDJ/RSI 等 | 计算逻辑 |
| 资金流向 | 个股主力资金追踪 | 数据源 |

### P2 - 高级功能

| 能力 | 说明 | 难点 |
|------|------|------|
| 回测验证 | 策略回测 | 数据量大 |
| 预警推送 | 实时风险预警 | 推送机制 |

---

## 设计原则

1. **层次分明** - 每个 skill 有明确的层次定位
2. **可组合** - skill 之间可以串联使用
3. **数据源稳定** - 优先选择免费、稳定的 API
4. **输出精简** - 返回关键信息，节省 token

---

## 数据源优先级

| 优先级 | 数据源 | 特点 |
|--------|--------|------|
| 1 | AKShare | 免费、稳定、覆盖广 |
| 2 | Tushare | 需积分、数据全 |
| 3 | RSSHub | 需自建、适合新闻 |
| 4 | 官方 API | 需付费、最可靠 |

---

## 参考资料

- [项目概述](../project-overview.md)
- [架构设计](../architecture/strategy-framework.md)
- [开发规范](../standards/development-standard.md)
