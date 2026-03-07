# 投资分析框架

> 本文档定义 OpenClaw-Alpha 的分析体系，指导 skill 开发方向。

---

## 分析层次

| 层次 | 核心问题 | 已有 Skill | 待补充 |
|------|----------|-----------|--------|
| **综合** | 市场整体如何？ | market_overview | - |
| **宏观** | 指数和情绪如何？ | index_analysis, market_sentiment | - |
| **中观** | 哪些板块热门？ | industry_trend, fund_flow_analysis, northbound_flow, lhb_tracker | - |
| **微观** | 买什么股票？ | stock_analysis, stock_screener, technical_indicators, etf_analysis, risk_alert, fundamental_analysis | - |
| **事件** | 有什么新闻/事件？ | news_driven_investment, limit_up_tracker, announcement_analysis | - |
| **组合** | 我的持仓怎么样？ | portfolio_analysis, watchlist_monitor | - |

---

## Skill 定位

### 综合层

| Skill | 定位 | 数据源 |
|-------|------|--------|
| **market_overview** | 一键式市场分析报告，整合各层次分析结果 | 复用其他 skill |

### 宏观层

| Skill | 定位 | 数据源 |
|-------|------|--------|
| **index_analysis** | 6 大核心指数分析，判断大盘趋势 | Tushare |
| **market_sentiment** | 涨跌停、资金流向，评估市场温度 | AKShare |
| **margin_trading** | 融资融券分析，监控市场杠杆水平 | AKShare |

### 中观层

| Skill | 定位 | 数据源 |
|-------|------|--------|
| **industry_trend** | 产业/概念板块热度追踪 | AKShare |
| **fund_flow_analysis** | 行业/概念资金流向排名 | AKShare |
| **northbound_flow** | 外资动向监控 | AKShare |
| **lhb_tracker** | 游资/机构动向（龙虎榜） | AKShare |

### 微观层

| Skill | 定位 | 数据源 |
|-------|------|--------|
| **stock_analysis** | 单只股票行情快照 | AKShare |
| **stock_fund_flow** | 个股主力资金流向分析 | AKShare |
| **stock_screener** | 多条件选股筛选 | AKShare |
| **technical_indicators** | 技术指标分析（MACD/RSI/KDJ等） | AKShare |
| **etf_analysis** | ETF 行情查询和筛选 | AKShare |
| **risk_alert** | 个股风险监控（业绩/价格/资金） | AKShare |
| **fundamental_analysis** | 基本面分析（PE/PB/ROE/财务指标） | AKShare |

### 事件层

| Skill | 定位 | 数据源 |
|-------|------|--------|
| **news_driven_investment** | 新闻驱动投资分析 | AKShare |
| **limit_up_tracker** | 涨停板追踪（连板/炸板） | AKShare |
| **announcement_analysis** | 上市公司公告解读 | AKShare |
| **restricted_release** | 限售解禁风险监控 | AKShare |

### 组合层

| Skill | 定位 | 数据源 |
|-------|------|--------|
| **portfolio_analysis** | 持仓结构分析（含盈亏计算） | AKShare |
| **watchlist_monitor** | 自选股监控 | AKShare |

---

## 层次关联

```
综合层（一键概览）
    ↓
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
0. **综合** - market_overview 一键生成市场报告（可选）
1. **宏观** - index_analysis 看指数，market_sentiment 看情绪，margin_trading 看杠杆
2. **中观** - industry_trend 找热门板块，northbound_flow 看外资偏好
3. **微观** - stock_screener 筛选个股，fundamental_analysis 看基本面，risk_alert 检查风险
4. **事件** - news_driven_investment 找催化，limit_up_tracker 追踪热点
5. **组合** - portfolio_analysis 管理持仓（含盈亏），watchlist_monitor 跟踪关注

---

## 行业轮动分析

基于"景气度 + 趋势 + 拥挤度"三维度框架：

| 维度 | 说明 | 理想状态 | 数据来源 |
|------|------|----------|----------|
| **景气度** | 行业盈利能力 | 高（ROE上行） | 财务数据 |
| **趋势** | 价格走势强度 | 高（上涨） | industry_trend |
| **拥挤度** | 市场参与程度 | 低（未过热） | 换手率分位 |

**黄金组合**：高景气度 + 高趋势 + 低拥挤度

详见：[行业轮动分析研究](../research/sector-rotation-analysis.md)

---

## 待补充能力

### P1 - 行业轮动

| 能力 | 说明 | 难度 | 依赖 |
|------|------|------|------|
| 行业景气度 | ROE趋势、利润增速追踪 | 中 | 财务数据 |
| 拥挤度指标 | 换手率分位、成交额占比 | 低 | 现有数据可计算 |

### P2 - 高级功能

| 能力 | 说明 | 难点 |
|------|------|------|
| 轮动评分 | 多因子综合评分模型 | 因子权重优化 |
| 回测验证 | 策略回测 | 数据量大 |
| 预警推送 | 实时风险预警 | 推送机制 |

---

## 已完成能力

| 能力 | 完成日期 | Skill |
|------|----------|-------|
| 限售解禁风险监控 | 2026-03-08 | restricted_release |
| 个股资金流向 | 2026-03-08 | stock_fund_flow |
| 融资融券分析 | 2026-03-08 | margin_trading |
| 综合分析 | 2026-03-08 | market_overview |
| 基本面分析 | 2026-03-07 | fundamental_analysis |
| 盈亏追踪 | 2026-03-07 | portfolio_analysis（已支持成本价输入） |
| 公告解读 | 2026-03-07 | announcement_analysis |

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

- [每日投资分析流程](daily-analysis-guide.md) - 快速上手指南
- [项目概述](../project-overview.md)
- [架构设计](../architecture/strategy-framework.md)
- [开发规范](../standards/development-standard.md)
