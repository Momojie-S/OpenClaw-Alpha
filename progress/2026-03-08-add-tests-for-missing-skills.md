# 任务：补充缺失测试

## 需求

发现 3 个 skill 缺少测试文件：
- margin_trading
- restricted_release
- backtest

## Phase 1: 分析代码结构
- [x] 检查 margin_trading 结构
- [x] 检查 restricted_release 结构
- [x] 检查 backtest 结构

## Phase 2: margin_trading 测试
- [x] 分析代码
- [x] 编写测试 - test_stock_margin_processor (10 个)
- [x] 编写测试 - test_market_margin_processor (7 个)

## Phase 3: restricted_release 测试
- [x] 分析代码
- [x] 编写测试 - test_restricted_release_fetcher (11 个)
- [x] 编写测试 - test_restricted_release_processor (11 个)

## Phase 4: backtest 测试
- [x] 分析代码
- [x] 编写测试 - test_backtest_strategies (13 个)
- [x] 编写测试 - test_data_adapter (6 个，2 个跳过)

## Phase 5: 全量测试
- [x] 运行全量测试 - 699 passed, 2 skipped

## 完成总结

### 测试覆盖提升

| 指标 | 之前 | 之后 | 增加 |
|------|------|------|------|
| 总测试数 | 639 | 699 | +60 |
| margin_trading | 0 | 17 | +17 |
| restricted_release | 0 | 22 | +22 |
| backtest | 0 | 21 | +21 |

### 新增测试内容

**margin_trading (17 个测试)**：
- stock_margin_processor: normalize_df, merge_stocks, format_text
- market_margin_processor: calculate_change_pct, get_latest_trading_day, format_text

**restricted_release (22 个测试)**：
- restricted_release_fetcher: _transform_detail, _transform_queue, _transform_summary, fetch
- restricted_release_processor: format_upcoming, format_queue, format_high_risk

**backtest (21 个测试)**：
- backtest_strategies: 策略注册表、基类方法、策略继承
- data_adapter: transform_to_backtrader, 数据验证

## 状态
- **当前阶段**：✅ 已完成
- **进度**：正常
- **完成时间**：2026-03-08 10:15
