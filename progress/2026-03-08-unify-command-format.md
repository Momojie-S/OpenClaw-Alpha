# 任务：统一命令格式为模块方式

## 需求

OpenClaw-Alpha 的命令格式不统一：
- `daily-analysis-guide.md` 使用 `python -m skills.xxx`（模块方式）
- 各 `SKILL.md` 使用 `python skills/xxx`（直接执行脚本）

需要统一为模块方式，保持一致性。

## Phase 1: 调研
- [x] 检查 daily-analysis-guide.md 的命令格式
- [x] 检查各 SKILL.md 的命令格式
- [x] 确认模块方式可用

## Phase 2: 更新 SKILL.md
- [x] announcement_analysis
- [x] etf_analysis
- [x] fund_flow_analysis
- [x] fundamental_analysis
- [x] index_analysis
- [x] industry_trend
- [x] lhb_tracker
- [x] limit_up_tracker
- [x] market_overview
- [x] market_sentiment
- [x] news_driven_investment
- [x] northbound_flow
- [x] portfolio_analysis
- [x] risk_alert
- [x] stock_analysis
- [x] stock_screener
- [x] technical_indicators
- [x] watchlist_monitor

**使用 sed 批量替换 + 手动修复特殊案例**：
- `python skills/xxx/scripts/yyy/yyy.py` → `python -m skills.xxx.scripts.yyy.yyy`
- `news_helper.py` → 模块方式
- `__main__.py` → 简化为 `python -m skills.xxx.scripts.yyy`

## Phase 3: 验证
- [x] 检查所有命令格式一致性 - 0 个 `python skills/` 残留
- [x] 验证模块方式可用 - `announcement_processor --help` 正常

## Phase 4: 提交
- [ ] git commit
- [ ] git push

## 状态
- **当前阶段**：Phase 4
- **进度**：正常
- **下一步**：提交变更

## 备注
开始时间：2026-03-08 02:05
