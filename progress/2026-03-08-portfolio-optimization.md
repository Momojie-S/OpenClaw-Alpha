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
- [x] git commit - f853671
- [x] git push

## 状态
- **当前阶段**：✅ 已完成
- **进度**：正常
- **完成时间**：2026-03-08 08:50

## 完成总结

### 新增功能

**1. 持仓相关性分析** - `correlation_processor`

**功能**：
- 计算股票相关系数矩阵
- 识别高相关股票对（相关性 > 0.7）
- 计算平均相关性和分散化评分
- 生成分散化等级和建议

**命令**：
```bash
uv run --env-file .env python -m skills.portfolio_analysis.scripts.correlation_processor.correlation_processor "000001,600000,002475" --days 60
```

**输出示例**：
```
持仓相关性分析报告
==================================================
分析日期: 2026-03-08
数据范围: 最近 60 个交易日
股票数量: 3

【分散化评估】
  平均相关性: 0.45
  分散化评分: 0.55
  分散程度: 适度分散

【高相关股票对】
  000001 ↔ 600000: 0.75 (高相关)

【投资建议】
  发现 1 对高相关股票；持仓分散度适中
```

**2. 风险贡献分解** - `risk_contribution_processor`

**功能**：
- 计算各股票对组合风险的贡献占比
- 计算风险集中度（Top 3 风险贡献）
- 提供风险平价权重建议
- 生成优化建议

**命令**：
```bash
uv run --env-file .env python -m skills.portfolio_analysis.scripts.risk_contribution_processor.risk_contribution_processor "000001:0.5,600000:0.3,002475:0.2" --days 60
```

**输出示例**：
```
风险贡献分析报告
==================================================
分析日期: 2026-03-08
组合波动率: 2.35%

【风险集中度】
  Top 3 风险贡献: 75.2%
  集中度等级: 风险集中

【风险贡献详情】
  000001: 权重 50.0% → 风险贡献 45.3% | 建议权重 35.8% (↓ 14.2%)
  600000: 权重 30.0% → 风险贡献 35.8% | 建议权重 38.5% (↑ 8.5%)
  002475: 权重 20.0% → 风险贡献 18.9% | 建议权重 25.7% (↑ 5.7%)

【投资建议】
  风险高度集中于 000001（45.3%）；建议降低 000001 仓位
```

### 技术实现

**理论依据**：
- 马科维茨均值-方差模型
- 风险平价理论

**核心算法**：
- 相关系数：Pearson 相关系数
- 风险贡献：RC_i = w_i * (Σw)_i / σ_p
- 风险平价：权重与波动率成反比

### 测试

- 新增 25 个单元测试
- 使用 mock 数据避免依赖外部 API
- 总测试数：50 passed（portfolio_analysis）

### 文档更新

- 更新 `portfolio_analysis/SKILL.md`
- 更新 `analysis-framework.md`（P5 全部完成）

### 提交记录

- Commit: f853671
- 内容：feat: 添加投资组合优化功能 - 持仓相关性与风险贡献分析

## 备注
开始时间：2026-03-08 08:05
完成时间：2026-03-08 08:50
耗时：45 分钟
