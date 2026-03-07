# 任务：ETF 分析 Skill (etf_analysis)

## 需求

实现一个 ETF 分析 skill，帮助用户获取和分析 ETF 基金数据，包括行情、筛选、历史数据查询等。

## Phase 1: 需求
- [x] 编写需求文档
  - 位置：`docs/etf-analysis/spec.md`
  - 内容：ETF 行情、筛选、历史数据

## Phase 2: 调研
- [x] 调研数据源（AKShare）
  - fund_etf_category_sina - 实时行情（1447 只 ETF）
  - fund_etf_hist_sina - 历史数据
  - fund_etf_scale_sse - 上交所规模数据
- [x] 确定技术方案：使用新浪数据源（稳定）

## Phase 3: 设计
- [x] 编写设计文档
  - 位置：`docs/etf-analysis/design.md`
  - 决策：直接在 Processor 中调用 AKShare（无需独立 Fetcher）

## Phase 4: 开发
- [x] 创建 skill 目录结构
- [x] 实现 EtfProcessor（行情获取、筛选、排序、历史数据）
- [x] 编写 SKILL.md

## Phase 5: 测试
- [x] 编写测试（15 个测试）
- [x] 运行测试，确保通过（15/15）
- [x] 全部测试通过（249 passed）

## Phase 6: 回顾
- [x] 文档已独立存放（docs/etf-analysis/），无需合并
- [x] 更新进度文件

## 完成总结

### 已完成

1. **需求文档** - `docs/etf-analysis/spec.md`
2. **设计文档** - `docs/etf-analysis/design.md`
3. **代码实现**
   - EtfProcessor（ETF 行情查询和分析）
   - SKILL.md 文档
4. **测试** - 15/15 通过
   - 筛选功能测试：8 个
   - 排序功能测试：4 个
   - 数据类测试：3 个

### 使用示例

```bash
# 查看今日涨幅榜
uv run --env-file .env python skills/etf_analysis/scripts/etf_processor/etf_processor.py --top-n 10

# 筛选涨幅 > 2% 且成交额 > 5 亿
uv run --env-file .env python skills/etf_analysis/scripts/etf_processor/etf_processor.py \
    --change-min 2 --amount-min 5

# 按关键词搜索
uv run --env-file .env python skills/etf_analysis/scripts/etf_processor/etf_processor.py \
    --keyword "创业板"

# 查看历史数据
uv run --env-file .env python skills/etf_analysis/scripts/etf_processor/etf_processor.py \
    --action history --symbol sz159915 --days 30
```

### 功能

| 功能 | 命令 |
|------|------|
| 实时行情 | `--action spot`（默认） |
| 历史数据 | `--action history --symbol xxx` |
| 涨跌幅筛选 | `--change-min / --change-max` |
| 成交额筛选 | `--amount-min` |
| 关键词搜索 | `--keyword` |
| 排序 | `--sort-by change/amount/price` |

### 技术决策

1. **数据源选择**：使用新浪财经（fund_etf_category_sina）而非东方财富，因为更稳定
2. **架构简化**：不需要独立 Fetcher，直接在 Processor 中调用 AKShare，减少代码复杂度
3. **成交额单位**：自动转换为亿元，方便阅读

## 备注
开始时间：2026-03-07 18:35
完成时间：2026-03-07 18:55
