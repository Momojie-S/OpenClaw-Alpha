# 智能投资决策框架研究

> 研究日期：2026-03-08
> 研究目的：探索如何让 LLM 更智能地组合使用现有分析能力，实现自动化投资决策支持

---

## 背景与目标

### 当前状态

OpenClaw-Alpha 已具备完整的投资分析能力：

| 层次 | Skill 数量 | 核心能力 |
|------|-----------|----------|
| 综合 | 1 | market_overview |
| 宏观 | 4 | index_analysis, market_sentiment, margin_trading, option_analysis |
| 中观 | 4 | industry_trend, fund_flow, northbound_flow, lhb_tracker |
| 微观 | 8 | stock_analysis, stock_screener, fundamental_analysis, technical_indicators 等 |
| 事件 | 4 | news_driven, limit_up_tracker, announcement_analysis, restricted_release |
| 组合 | 2 | portfolio_analysis, watchlist_monitor |
| 预警 | 1 | alert_monitor |

**总计**：24 个 Skill，覆盖完整分析链条

### 问题

1. **选择困难**：面对这么多 Skill，用户不知道从哪个开始
2. **组合复杂**：不同场景需要不同的 Skill 组合
3. **解读门槛**：输出结果需要专业知识解读

### 目标

设计一个**智能决策框架**，让 LLM：
1. 理解用户意图
2. 自动选择合适的分析工具
3. 组合多个 Skill 的结果
4. 给出可操作的建议

---

## 设计思路

### 核心原则

1. **意图驱动**：从用户问题出发，而非从工具出发
2. **渐进式分析**：从宏观到微观，层层深入
3. **置信度透明**：告诉用户结论的置信度和依据
4. **可解释性**：每个结论都有明确的分析路径

### 决策树模型

```
用户问题
    │
    ├── 市场整体？ ──────────────────→ market_overview
    │
    ├── 指数趋势？ ──────────────────→ index_analysis + option_analysis
    │
    ├── 板块选择？ ──────────────────→ industry_trend + fund_flow
    │   │
    │   ├── 景气度？ ──→ prosperity_processor
    │   ├── 拥挤度？ ──→ crowdedness_processor
    │   └── 轮动评分？ ─→ rotation_score_processor
    │
    ├── 选股？ ──────────────────────→ stock_screener + fundamental_analysis
    │   │
    │   ├── 基本面？ ──→ fundamental_analysis
    │   ├── 技术面？ ──→ technical_indicators
    │   └── 资金面？ ──→ stock_fund_flow
    │
    ├── 个股分析？ ──────────────────→ stock_analysis + risk_alert
    │
    ├── 持仓管理？ ──────────────────→ portfolio_analysis + watchlist_monitor
    │   │
    │   ├── 盈亏？ ───→ portfolio_processor
    │   ├── 相关性？ ─→ correlation_processor
    │   └── 风险贡献？→ risk_contribution_processor
    │
    ├── 风险预警？ ──────────────────→ alert_monitor + risk_alert
    │
    └── 事件驱动？ ──────────────────→ news_driven + announcement_analysis
        │
        ├── 涨停追踪？→ limit_up_tracker
        └── 解禁监控？→ restricted_release
```

---

## 智能场景识别

### 场景定义

| 场景 | 用户问题示例 | 推荐分析链 |
|------|-------------|-----------|
| **早盘准备** | "今天市场怎么样？" | market_overview(quick) |
| **选股** | "帮我选几只股票" | stock_screener + fundamental_analysis |
| **个股诊断** | "分析一下 XX 股票" | stock_analysis + fundamental + technical + risk |
| **板块轮动** | "现在应该买什么板块？" | industry_trend(轮动评分) + fund_flow |
| **持仓检查** | "我的持仓有问题吗？" | portfolio_analysis + alert_monitor |
| **风险预警** | "有什么风险要注意？" | alert_monitor + risk_alert |
| **事件追踪** | "最近有什么热点？" | news_driven + limit_up_tracker |
| **外资动向** | "北向资金在买什么？" | northbound_flow + fund_flow |

### 意图识别 Prompt 模板

```markdown
用户问题：{user_question}

请识别用户意图，选择最匹配的分析场景：
1. 早盘准备 - 快速了解市场状态
2. 选股 - 筛选符合条件的股票
3. 个股诊断 - 深入分析单只股票
4. 板块轮动 - 判断当前热门板块
5. 持仓检查 - 评估持仓风险
6. 风险预警 - 识别潜在风险
7. 事件追踪 - 追踪市场热点
8. 外资动向 - 监控外资流向

输出 JSON：
{
  "scene": "场景名称",
  "confidence": 0.9,
  "parameters": {
    "stock_code": "000001",  // 如有
    "top_n": 10
  }
}
```

---

## 组合分析模式

### 模式 1：快速诊断

**场景**：用户想快速了解某只股票

**分析链**：
```
stock_analysis（行情快照）
    ↓
fundamental_analysis（基本面）
    ↓
technical_indicators（技术面）
    ↓
risk_alert（风险检查）
```

**输出**：综合诊断报告

### 模式 2：深度选股

**场景**：用户想筛选符合条件的股票

**分析链**：
```
stock_screener（筛选）
    ↓
fundamental_analysis（基本面过滤）
    ↓
technical_indicators（技术面确认）
    ↓
stock_fund_flow（资金面验证）
```

**输出**：候选股票列表 + 每只股票的分析报告

### 模式 3：板块轮动

**场景**：用户想判断当前应该配置什么板块

**分析链**：
```
industry_trend（板块热度）
    ↓
prosperity_processor（景气度）
    ↓
crowdedness_processor（拥挤度）
    ↓
rotation_score_processor（综合评分）
    ↓
fund_flow（资金验证）
```

**输出**：板块推荐 + 配置建议

### 模式 4：持仓体检

**场景**：用户想评估当前持仓

**分析链**：
```
portfolio_analysis（持仓分析）
    ↓
correlation_processor（相关性）
    ↓
risk_contribution_processor（风险贡献）
    ↓
alert_monitor（风险预警）
```

**输出**：持仓健康报告 + 调仓建议

---

## 输出模板

### 综合报告模板

```markdown
# {场景} 分析报告

## 核心结论

{一句话结论}

---

## 分析依据

| 维度 | 指标 | 结论 |
|------|------|------|
| 基本面 | PE/PB/ROE | {结论} |
| 技术面 | MACD/RSI | {结论} |
| 资金面 | 主力/北向 | {结论} |
| 风险 | 风险评级 | {结论} |

---

## 详细分析

### 1. {分析项 1}
{详细内容}

### 2. {分析项 2}
{详细内容}

---

## 操作建议

{可操作的建议}

## 风险提示

{风险因素}
```

---

## 实现建议

### 短期

1. **场景 Prompt 优化**
   - 为每个场景设计专门的 Prompt
   - 明确分析链和输出格式

2. **输出格式标准化**
   - 统一 JSON 输出格式
   - 便于 LLM 解析和组合

### 中期

1. **意图识别模块**
   - 基于关键词 + 语义的意图识别
   - 参数提取（股票代码、日期等）

2. **分析编排引擎**
   - 自动选择和组合 Skill
   - 处理依赖关系

### 长期

1. **学习型推荐**
   - 记录用户偏好
   - 个性化分析建议

2. **闭环优化**
   - 收集反馈
   - 持续优化推荐准确性

---

## 示例对话

### 示例 1：选股场景

```
用户：帮我选几只市盈率低于 20 的股票

Alpha：我来帮你筛选。
[执行 stock_screener --pe-max 20 --top-n 10]

找到 10 只符合条件的股票，我来进一步分析基本面：
[执行 fundamental_analysis 对 Top 5]

综合分析结果：

| 股票 | PE | PB | ROE | 评级 |
|------|-----|-----|-----|------|
| XX银行 | 5.2 | 0.6 | 12% | ⭐⭐⭐ |
| YY股份 | 8.5 | 1.2 | 15% | ⭐⭐⭐⭐ |

推荐：YY股份（基本面更优）

风险提示：低 PE 可能反映市场悲观预期
```

### 示例 2：个股诊断场景

```
用户：分析一下贵州茅台

Alpha：我来全面分析贵州茅台（600519）。
[执行 stock_analysis + fundamental_analysis + technical_indicators + risk_alert]

## 贵州茅台 综合诊断

### 核心结论
基本面优秀，技术面中性，资金面偏弱，整体评级：**谨慎持有**

### 分析依据
| 维度 | 评级 | 关键指标 |
|------|------|----------|
| 基本面 | 优秀 | ROE 32%, 毛利率 91% |
| 技术面 | 中性 | MACD 死叉, RSI 45 |
| 资金面 | 偏弱 | 主力近5日流出 12 亿 |
| 风险 | 低 | 无重大风险 |

### 操作建议
- 持有者：可继续持有，设置止损位 1500
- 意向买入：等待技术面企稳后再介入

### 风险提示
- 近期主力资金持续流出
- 技术面尚未企稳
```

---

## 总结

1. **现有能力充足**：24 个 Skill 已覆盖完整分析链条
2. **关键在组合**：让 LLM 智能选择和组合 Skill
3. **场景化设计**：针对不同场景设计分析链
4. **输出标准化**：统一格式便于解析和展示
5. **渐进式增强**：从规则到学习，逐步优化
