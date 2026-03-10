# Skill 自检记录

记录所有 skill 的自检历史和后续待办。

---

## 自检总表

| Skill ID | 上次自检时间 | 后续待办 |
|----------|--------------|----------|
| openclaw_alpha_alert_monitor | - | - |
| openclaw_alpha_announcement_analysis | - | - |
| openclaw_alpha_backtest | - | - |
| openclaw_alpha_etf_analysis | - | - |
| openclaw_alpha_fund_flow_analysis | - | - |
| openclaw_alpha_fundamental_analysis | - | - |
| openclaw_alpha_index_analysis | - | - |
| openclaw_alpha_industry_trend | - | - |
| openclaw_alpha_lhb_tracker | - | - |
| openclaw_alpha_limit_up_tracker | - | - |
| openclaw_alpha_margin_trading | - | - |
| openclaw_alpha_market_overview | 2026-03-10 | ✅ 已修复 bug |
| openclaw_alpha_market_sentiment | 2026-03-10 | ✅ 已修复 bug |
| openclaw_alpha_news_driven_investment | - | - |
| openclaw_alpha_northbound_flow | - | - |
| openclaw_alpha_option_analysis | - | - |
| openclaw_alpha_portfolio_analysis | - | - |
| openclaw_alpha_restricted_release | - | - |
| openclaw_alpha_risk_alert | - | - |
| openclaw_alpha_smart_dip | - | - |
| openclaw_alpha_stock_analysis | - | - |
| openclaw_alpha_stock_compare | - | - |
| openclaw_alpha_stock_fund_flow | - | - |
| openclaw_alpha_stock_screener | - | - |
| openclaw_alpha_technical_indicators | - | - |
| openclaw_alpha_theme_speculation | - | - |
| openclaw_alpha_watchlist_monitor | - | - |

---

## 自检详情

### 2026-03-10: market_overview + market_sentiment

**发现问题**：
- `limit_fetcher/tushare_impl.py` 返回字段名与 AKShare 实现不一致
- Tushare 返回 `up_count`/`down_count`，AKShare 返回 `limit_up`/`limit_down`
- 导致 `sentiment_processor.py` 访问字段时抛出 `KeyError: 'limit_up'`

**修复内容**：
- 统一 `limit_fetcher/tushare_impl.py` 的返回字段名为 `limit_up`/`limit_down`/`break_board`

**验证结果**：
- ✅ `trading_calendar_processor` 正常运行
- ✅ `overview_processor --mode quick --auto-fetch` 正常运行

---

## 更新说明

- 每次自检完成后，更新对应 skill 的"上次自检时间"和"后续待办"
- 如果有改进任务，在"后续待办"中填写进度文件路径
- 改进完成后，清空"后续待办"
