# 任务：龙虎榜追踪 Skill (lhb_tracker)

## 需求

实现龙虎榜追踪 skill，追踪游资和机构动向，与北向资金形成内外资完整的资金追踪体系。

## Phase 1: 需求
- [x] 编写需求文档
  - 位置：`docs/lhb-tracker/spec.md`

## Phase 2: 设计
- [x] 调研技术方案，编写设计文档
  - 位置：`docs/lhb-tracker/design.md`
  - 决策：使用 AKShare（免费）
- [x] 检查是否需要外部 API 调用
  - 需要：AKShare stock_lhb_detail_em, stock_lhb_stock_detail_em

## Phase 3: API 文档
- 跳过（AKShare 接口稳定且免费）

## Phase 4: 开发
- [x] 创建 skill 目录结构
- [x] 实现 LhbFetcher 基类和入口
- [x] 实现 LhbFetcherAkshare
- [x] 实现 LhbProcessor
- [x] 编写 SKILL.md

## Phase 5: 调试
- [x] 调试 AKShare 实现 - 正常
- [x] Processor 端到端测试 - 正常

## Phase 6: 测试
- [x] 编写 Fetcher 测试 - 4 个测试
- [x] 编写 Processor 测试 - 6 个测试
- [x] 运行测试，确保全部通过 - 10/10 通过

## Phase 7: 文档合并
- [x] 文档已独立存放（docs/lhb-tracker/），无需合并

## 完成总结

### 已完成

1. **需求文档** - `docs/lhb-tracker/spec.md`
2. **设计文档** - `docs/lhb-tracker/design.md`
3. **代码实现**
   - LhbFetcherAkshare（龙虎榜数据获取）
   - LhbProcessor（龙虎榜分析）
   - SKILL.md 文档
4. **测试** - 10/10 通过
   - Fetcher 测试: 4 个测试
   - Processor 测试: 6 个测试

### 使用示例

```bash
# 查看每日龙虎榜
uv run --env-file .env python skills/lhb_tracker/scripts/lhb_processor/lhb_processor.py --action daily --top-n 10

# 查看个股龙虎榜历史
uv run --env-file .env python skills/lhb_tracker/scripts/lhb_processor/lhb_processor.py --action stock --symbol 000001 --days 5
```

## 备注

开始时间：2026-03-07 05:40
完成时间：2026-03-07 06:20
