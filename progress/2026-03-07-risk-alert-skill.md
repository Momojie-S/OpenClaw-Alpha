# 任务：风险监控 Skill (risk_alert)

## 需求

实现一个风险监控 skill，帮助投资者识别股票风险信号，包括业绩风险、异常波动、资金流出等。

## Phase 1: 需求
- [x] 编写需求文档
  - 位置：`docs/risk-alert/spec.md`
  - 内容：定义风险类型、监控指标、预警规则

## Phase 2: 设计
- [x] 调研技术方案，编写设计文档
  - 位置：`docs/risk-alert/design.md`
  - 决策：使用 AKShare 作为唯一数据源（免费）
- [x] 检查是否需要外部 API 调用
  - 需要：AKShare stock_yjyg_em, stock_zh_a_hist, stock_individual_fund_flow

## Phase 3: API 文档
- 跳过（使用已知 AKShare 接口）

## Phase 4: 开发
- [x] 创建 skill 目录结构
- [x] 实现 ForecastFetcher（业绩预告）
- [x] 实现 RiskProcessor（风险分析）
- [x] 编写 SKILL.md

## Phase 5: 调试
- [x] 调试 ForecastFetcher AKShare 实现 - 正常
- [x] 调试 RiskProcessor 端到端 - 正常

## Phase 6: 测试
- [x] 编写 ForecastFetcher 测试 - 4 个测试
- [x] 编写 RiskProcessor 测试 - 12 个测试
- [x] 运行测试，确保全部通过 - 16/16 通过

## Phase 7: 文档合并
- [x] 文档已独立存放（docs/risk-alert/），无需合并

## 完成总结

### 已完成

1. **需求文档** - `docs/risk-alert/spec.md`
2. **设计文档** - `docs/risk-alert/design.md`
3. **代码实现**
   - ForecastFetcher（业绩预告数据获取）
   - RiskProcessor（风险分析）
   - SKILL.md 文档
4. **测试** - 16/16 通过
   - ForecastFetcher 测试: 4 个测试
   - RiskProcessor 测试: 12 个测试（风险评级、建议生成、各类风险检查）

### 使用示例

```bash
# 检查个股风险
uv run --env-file .env python skills/risk_alert/scripts/risk_processor/risk_processor.py 000001

# 指定日期和天数
uv run --env-file .env python skills/risk_alert/scripts/risk_processor/risk_processor.py 002364 --date 2026-03-07 --days 5
```

### 功能

| 风险类型 | 检查内容 |
|---------|---------|
| 业绩风险 | 业绩预告类型（首亏、预减等） |
| 价格风险 | 连续下跌、单日大跌 |
| 资金风险 | 主力资金持续流出 |

### 待后续

- Phase 2：全市场风险扫描
- Phase 2：大股东减持监控
- Phase 2：股权质押风险

## 备注
开始时间：2026-03-07 07:10
完成时间：2026-03-07 07:45

**注意**：AKShare 部分接口（东方财富）网络不稳定，可能需要重试。这是外部因素，不影响核心逻辑。
