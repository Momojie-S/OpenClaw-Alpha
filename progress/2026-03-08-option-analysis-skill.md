# 任务：期权分析 Skill

## 需求

分析框架中 P4 优先级能力。期权分析是重要的市场情绪指标来源，PCR 和隐含波动率可判断市场多空情绪。

**分析思路**：
- 利用 AKShare 免费接口获取期权数据
- 核心功能：期权情绪分析（PCR + IV）+ 期权市场概况
- 属于宏观层，补充市场情绪判断

## Phase 1: 研究
- [x] 调研 AKShare 期权接口
- [x] 编写研究报告 - docs/research/option-analysis-research.md

## Phase 2: 需求与设计
- [x] 研究报告中已包含设计

## Phase 3: 开发
- [x] 创建 option_analysis skill 目录
- [x] 实现 option_data_fetcher（数据获取）
- [x] 实现 sentiment_processor（情绪分析）
- [x] 实现 market_overview_processor（市场概况）
- [x] 编写 SKILL.md

## Phase 4: 验证
- [x] 语法检查
- [x] 功能测试 - sentiment_processor 测试通过

## Phase 5: 提交
- [ ] git commit
- [ ] git push

## 状态
- **当前阶段**：Phase 5 - 提交
- **进度**：正常
- **下一步**：git commit

## 备注
开始时间：2026-03-08 07:35
