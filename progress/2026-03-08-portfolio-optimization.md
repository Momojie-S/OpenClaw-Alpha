# 任务：投资组合优化功能

## 需求

基于投资组合优化研究（docs/research/portfolio-optimization-research.md），为 portfolio_analysis skill 增强能力。

**核心功能**：
1. 持仓相关性分析 - 计算股票相关系数矩阵，评估分散程度
2. 风险贡献分解 - 各股票对组合风险的贡献占比

**分析思路**：
- 获取持仓股票历史价格数据
- 计算收益率协方差矩阵
- 计算相关系数和风险贡献
- 生成分散化评分和优化建议

## Phase 1: 调研
- [x] 阅读研究文档
- [x] 确认实现方案

## Phase 2: 持仓相关性分析
- [x] 创建 correlation_fetcher
- [x] 实现历史价格获取
- [x] 实现收益率计算
- [x] 实现相关系数矩阵计算
- [x] 创建 correlation_processor
- [x] 实现分散化评分

## Phase 3: 风险贡献分解
- [x] 创建 risk_contribution_processor
- [x] 实现风险贡献计算
- [x] 实现风险平价权重建议
- [x] 实现风险集中度指标

## Phase 4: 测试
- [x] 编写 correlation_fetcher 测试 - 6 个测试
- [x] 编写 correlation_processor 测试 - 10 个测试
- [x] 编写 risk_contribution_processor 测试 - 9 个测试
- [x] 运行全量测试 - 50 passed

## Phase 5: 文档更新
- [x] 更新 portfolio_analysis SKILL.md
- [x] 更新 analysis-framework.md

## Phase 6: 提交
- [ ] git commit
- [ ] git push

## 状态
- **当前阶段**：Phase 6 - 提交
- **进度**：正常
- **下一步**：git commit

## 备注
开始时间：2026-03-08 08:05
完成时间：2026-03-08 08:45
