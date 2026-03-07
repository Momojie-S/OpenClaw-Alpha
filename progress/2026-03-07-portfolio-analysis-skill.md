# 任务：持仓分析 Skill (portfolio_analysis)

## 需求

实现一个持仓分析 skill，帮助用户分析投资组合的结构、风险敞口和分散程度。

## Phase 1: 需求
- [x] 编写需求文档
  - 位置：`docs/portfolio-analysis/spec.md`
  - 内容：持仓输入格式、分析维度、风险规则

## Phase 2: 设计
- [x] 调研技术方案，编写设计文档
  - 位置：`docs/portfolio-analysis/design.md`
  - 决策：复用 stock_screener 的 StockSpotFetcher，新建 IndustryInfoFetcher
- [x] 检查是否需要外部 API 调用
  - 需要：AKShare stock_individual_info_em（行业信息）

## Phase 3: API 文档
- 跳过（使用已知 AKShare 接口）

## Phase 4: 开发
- [x] 创建 skill 目录结构
- [x] 实现 IndustryInfoFetcher（AKShare）
- [x] 实现 PortfolioProcessor
- [x] 编写 SKILL.md

## Phase 5: 调试
- [x] IndustryInfoFetcher AKShare 实现 - 网络不稳定（外部因素）
- [x] PortfolioProcessor 逻辑测试 - 正常

## Phase 6: 测试
- [x] 编写 IndustryInfoFetcher 测试 - 6 个测试
- [x] 编写 PortfolioProcessor 测试 - 19 个测试
- [x] 运行测试，确保全部通过 - 25/25 通过

## Phase 7: 文档合并
- [x] 文档已独立存放（docs/portfolio-analysis/），无需合并

## 完成总结

### 已完成

1. **需求文档** - `docs/portfolio-analysis/spec.md`
2. **设计文档** - `docs/portfolio-analysis/design.md`
3. **代码实现**
   - IndustryInfoFetcher（行业信息获取）
   - PortfolioProcessor（持仓分析）
   - SKILL.md 文档
4. **测试** - 25/25 通过
   - IndustryInfoFetcher 测试: 6 个测试
   - PortfolioProcessor 测试: 19 个测试

### 使用示例

```bash
# 命令行输入
uv run --env-file .env python skills/portfolio_analysis/scripts/portfolio_processor/portfolio_processor.py \
    --holdings "000001:1000:12.5,600000:500:8.2"

# JSON 文件输入
uv run --env-file .env python skills/portfolio_analysis/scripts/portfolio_processor/portfolio_processor.py \
    --file portfolio.json
```

### 功能

| 维度 | 内容 |
|------|------|
| 持仓结构 | 各股票权重、Top 5 |
| 行业分布 | 行业权重、HHI 指数 |
| 盈亏分析 | 各股盈亏、总盈亏 |
| 风险提示 | 集中度、持仓数量检查 |

## 备注
开始时间：2026-03-07 08:10
完成时间：2026-03-07 08:40
