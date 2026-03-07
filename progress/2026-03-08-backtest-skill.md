# 任务：策略回测功能

## 需求

分析框架中 P2 优先级能力。策略回测用于验证投资策略的历史表现，是量化投资的核心工具。

**分析思路**：
- 使用 Backtrader 框架实现回测引擎
- 复用现有 Fetcher 获取历史数据
- MVP 聚焦单股票 + 基础策略

## Phase 1: 研究
- [x] 调研主流回测框架（Backtrader、Zipline、VectorBT）
- [x] 评估数据源支持（Tushare、AKShare）
- [x] 编写研究报告 - docs/research/backtest-research.md

## Phase 2: 需求
- [x] 编写需求文档 - docs/skills/backtest/spec.md
- [ ] 编写设计文档（如需要）

## Phase 3: 开发
- [ ] 创建 backtest skill 目录
- [ ] 实现数据转换模块（data_adapter.py）
- [ ] 实现策略基类（base_strategy.py）
- [ ] 实现均线交叉策略（ma_cross_strategy.py）
- [ ] 实现回测主流程（backtest_processor.py）
- [ ] 编写 SKILL.md

## Phase 4: 验证
- [ ] 单元测试
- [ ] 运行脚本测试

## Phase 5: 文档更新
- [ ] 更新 analysis-framework.md
- [ ] 编写使用示例

## Phase 6: 提交
- [ ] git commit
- [ ] git push

## 状态
- **当前阶段**：Phase 2 已完成
- **进度**：正常
- **下一步**：开发数据转换模块

## 备注
开始时间：2026-03-08 05:30

## 研究总结

### 技术选型

**Backtrader** - 最佳选择
- 灵活、模块化
- 支持 PandasData（直接使用我们的数据）
- 丰富的技术指标和分析器
- 活跃的社区

### 数据源

已有支持：
- ✅ Tushare - 历史数据完整、稳定
- ✅ AKShare - 免费、数据丰富

### MVP 范围

**包含**：
- 单股票回测
- 均线交叉策略
- 关键指标输出（收益率、夏普、回撤）
- 交易记录保存

**不包含**：
- 多股票组合
- 参数优化
- 可视化图表

### 预计时间

- 数据转换：2 小时
- 策略实现：2 小时
- 回测流程：2 小时
- 测试：2 小时
- 文档：1 小时
- **总计**：9 小时

### 风险

| 风险 | 缓解措施 |
|------|----------|
| A股涨跌停处理复杂 | MVP 先不做，后续优化 |
| 历史数据量大 | 限制回测时间范围（默认 1 年） |
| 策略过拟合 | 警告用户，历史表现不代表未来 |
