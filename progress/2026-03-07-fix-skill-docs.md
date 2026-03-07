# 任务：修复 SKILL.md 文档路径错误

## 需求

多个 skill 的 SKILL.md 中存在路径错误，导致命令无法执行。

## 问题列表

| Skill | 问题 |
|-------|------|
| industry_trend | 路径使用 `industry-trend`（连字符），实际是 `industry_trend`（下划线）|
| limit_up_tracker | 直接运行报错，需用模块方式 |
| news_monitor | 与 news_driven_investment 重复，应删除 |

## Phase 1: 修复 industry_trend SKILL.md
- [x] 修复所有路径错误（5 处）
- [x] 改用模块方式运行（更稳定）

## Phase 2: 修复 limit_up_tracker SKILL.md
- [x] 更新命令示例为模块方式（5 处）

## Phase 3: 清理重复 skill
- [x] 删除 news_monitor skill（与 news_driven_investment 重复）

## Phase 4: 修复 news_driven_investment 示例
- [x] 修复 industry_trend 命令路径
- [x] 移除 stock_screener 不存在的 --industry 参数

## Phase 5: 验证
- [x] 测试 industry_trend 命令 - 正常
- [x] 测试 limit_up_tracker 命令 - 正常
- [x] 确认 news_monitor 已删除
- [x] 检查所有 SKILL.md 命令路径 - 无问题

## 状态
- **当前阶段**：完成
- **进度**：正常
- **完成时间**：2026-03-07 19:55

## 备注
开始时间：2026-03-07 19:35
