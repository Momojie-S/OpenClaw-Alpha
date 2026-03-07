# 任务：添加融资融券分析 skill

## 需求

分析框架中缺少融资融券分析能力。融资融券是 A 股市场的重要杠杆工具，可以反映市场情绪和风险水平。

**分析思路**：
- 使用 AKShare 的融资融券数据接口
- 实现市场汇总和个股明细两个维度
- 计算融资余额环比变化，判断杠杆水平

## Phase 1: 调研
- [x] 检查 AKShare 可用的融资融券接口
- [x] 测试数据获取和格式

## Phase 2: 开发
- [x] 创建 market_margin_processor（市场汇总）
- [x] 创建 stock_margin_processor（个股明细）
- [x] 编写 SKILL.md

## Phase 3: 验证
- [x] 测试市场汇总命令 - 正常
- [x] 测试个股融资 Top N - 正常
- [x] 测试个股融券 Top N - 正常
- [x] 运行测试 - 377 passed

## Phase 4: 更新文档
- [x] 更新 analysis-framework.md
- [x] 添加到已完成能力列表

## Phase 5: 提交
- [x] git commit - 5d32571
- [x] git push

## 状态
- **当前阶段**：✅ 已完成
- **进度**：正常
- **完成时间**：2026-03-08 03:30

## 完成总结

### 新增 Skill

**margin_trading** - 融资融券分析

两个 Processor：
1. **market_margin_processor** - 市场融资融券汇总
   - 沪深两市融资余额
   - 融资余额环比变化
   - 杠杆水平判断（高/正常/低）

2. **stock_margin_processor** - 个股融资融券明细
   - 融资余额 Top N
   - 融券余额 Top N

### 数据源

- 沪市汇总：`ak.macro_china_market_margin_sh()`
- 深市汇总：`ak.macro_china_market_margin_sz()`
- 沪市个股：`ak.stock_margin_detail_sse(date)`
- 深市个股：`ak.stock_margin_detail_szse(date)`（不稳定）

### 提交记录

- Commit: 5d32571
- 内容：feat: 添加融资融券分析 skill
