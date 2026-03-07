# 任务：选股筛选器 Skill (stock_screener)

## 需求

实现一个选股筛选器 skill，帮助用户按多种条件筛选股票，快速找到符合投资标准的标的。

## Phase 1: 需求
- [x] 编写需求文档
  - 位置：`docs/stock-screener/spec.md`
  - 完成：定义筛选条件、预设策略、验收标准

## Phase 2: 设计
- [x] 调研技术方案，编写设计文档
  - 位置：`docs/stock-screener/design.md`
  - 决策：使用 AKShare stock_zh_a_spot_em 接口
- [x] 检查是否需要外部 API 调用
  - 使用已知接口，跳过 API 文档

## Phase 3: API 文档
- 跳过（使用已知 AKShare 接口）

## Phase 4: 开发
- [x] 创建 skill 目录结构
- [x] 实现 StockSpotFetcher（AKShare）
- [x] 实现 ScreenerProcessor
- [x] 编写 SKILL.md

## Phase 5: 调试
- [x] AKShare API 调试 - 网络不稳定（外部因素）
- [x] 使用 fixture 数据完成转换逻辑测试

## Phase 6: 测试
- [x] 编写 Fetcher 测试 - 5 个测试
- [x] 编写 Processor 测试 - 17 个测试
- [x] 运行测试，确保全部通过 - 22/22 通过

## Phase 7: 文档合并
- [x] 文档已独立存放（docs/stock-screener/），无需合并

## 完成总结

### 已完成

1. **需求文档** - `docs/stock-screener/spec.md`
2. **设计文档** - `docs/stock-screener/design.md`
3. **代码实现**
   - StockSpotFetcher（全市场行情获取）
   - ScreenerProcessor（选股筛选）
   - SKILL.md 文档
4. **测试** - 22/22 通过
   - StockSpotFetcher: 5 个测试
   - ScreenerProcessor: 17 个测试（筛选、排序、策略）

### 预设策略

| 策略 | 条件 |
|------|------|
| volume_breakout | 涨幅 > 3%，换手率 > 5%，成交额 > 2 亿 |
| pullback | 涨幅 -5% ~ 0%，换手率 < 3% |
| leader | 涨幅 > 5%，成交额 > 10 亿，市值 > 100 亿 |
| small_active | 换手率 > 8%，市值 < 50 亿 |
| blue_chip | 市值 > 500 亿，换手率 < 2% |

### 使用示例

```bash
# 使用预设策略
uv run --env-file .env python skills/stock_screener/scripts/screener_processor/screener_processor.py \
    --strategy volume_breakout --top-n 10

# 自定义筛选
uv run --env-file .env python skills/stock_screener/scripts/screener_processor/screener_processor.py \
    --change-min 3 --turnover-min 5 --amount-min 2 --top-n 20

# 列出可用策略
uv run --env-file .env python skills/stock_screener/scripts/screener_processor/screener_processor.py --list-strategies
```

### 待后续

- 网络稳定时验证真实 API 调用
- Phase 2：增加财务指标筛选（需要高积分 API）
- Phase 3：增加技术指标筛选

## 备注

开始时间：2026-03-07 06:10
完成时间：2026-03-07 06:50

**注意**：AKShare 全市场行情接口（stock_zh_a_spot_em）网络不稳定，东方财富接口有限流问题。这是外部因素，不影响核心逻辑。
