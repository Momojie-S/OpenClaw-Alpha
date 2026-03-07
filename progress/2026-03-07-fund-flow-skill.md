# 任务：资金流向分析 Skill (fund_flow_analysis)

## 需求

实现资金流向分析 skill，提供主力资金、行业资金、概念资金等多维度分析能力。

**分析思路**：AKShare 提供丰富的资金流向接口，可以整合成统一的资金流向分析工具。

## Phase 1: 需求
- [x] 编写需求文档 - `docs/skills/fund-flow-analysis/spec.md`

## Phase 2: 调研
**调研方向**：API调研（资金流向接口）
- [x] 调研 AKShare 资金流向相关接口
- [x] 确定技术方案：直接调用 AKShare（stock_fund_flow_industry/concept）

## Phase 3: 文档
**所需文档**：需求文档、设计文档
- [x] 编写需求文档 - `docs/skills/fund-flow-analysis/spec.md`
- [x] 编写设计文档 - `docs/skills/fund-flow-analysis/design.md`

## Phase 4: 开发
**开发任务**：
- [x] 创建 skill 目录结构
- [x] 实现 FundFlowProcessor（行业/概念资金流向）
- [x] 编写 SKILL.md

**功能**：
- 行业资金流向查询
- 概念资金流向查询
- 多时间周期（今日/3日/5日/10日/20日）
- 排序（净额/涨幅/流入）
- 筛选（最小净额）
- Top N 输出

## Phase 5: 验证
**验证方式**：API调试 + 单元测试
- [x] 调试 API（网络正常）
- [x] 编写单元测试（14 个测试）
- [x] 修复测试 mock 路径错误
- [x] 运行测试 - 14/14 通过

## Phase 6: 回顾
- [x] 文档已独立存放
- [x] 总结经验教训

**经验教训**：
- Mock 路径应 patch 模块被导入的位置，而非定义位置
- 测试文件中 `import akshare as ak`，mock 路径应为 `...fund_flow_processor.ak.xxx`

## Phase 7: 提交
- [x] git commit (d3b0808)
- [x] git push

## 完成总结

已完成资金流向分析 skill 的开发、测试和提交。

**提交记录**: d3b0808 feat: 新增资金流向分析 skill

## 状态
- **当前阶段**：✅ 已完成
- **进度**：正常
