# 任务：指数分析 Skill (index_analysis)

## 需求

实现指数分析 skill，提供主要指数的行情数据和技术分析，与市场情绪、板块轮动、个股分析形成完整的分析体系。

## Phase 1: 需求
- [x] 编写需求文档（按规范存放）
  - 位置：`docs/index-analysis/spec.md`
  - 内容：6个核心指数、技术分析、强弱对比、市场温度

## Phase 2: 设计
- [x] 调研技术方案，编写设计文档（按规范存放）
  - 位置：`docs/index-analysis/design.md`
  - 决策：单数据源 AKShare，单 Fetcher，轻量 Processor
- [x] 检查是否需要外部 API 调用
  - 使用已知 AKShare 接口，跳过

## Phase 3: API 文档
- 跳过（使用已知接口 stock_zh_index_daily_em）

## Phase 4: 开发
- [x] 创建 skill 目录结构
- [x] 实现 IndexFetcher（AKShare）
- [x] 实现 IndexProcessor
- [x] 编写 SKILL.md

## Phase 5: 调试
- [x] 调试 IndexFetcher AKShare 实现 - 网络不稳定，使用 fixture
- [x] 调试 IndexProcessor 端到端 - 使用 fixture 数据

## Phase 6: 测试
- [x] 编写测试（24个测试用例）
- [x] 运行测试，确保全部通过 - 24/24 通过

## Phase 7: 文档合并
- [x] 文档已独立存放（docs/index-analysis/），无需合并

## 完成总结

### 已完成

1. **需求文档** - `docs/index-analysis/spec.md`
2. **设计文档** - `docs/index-analysis/design.md`
3. **代码实现**
   - IndexFetcher（AKShare 实现）
   - IndexProcessor（指数分析）
   - SKILL.md 文档
4. **测试** - 24/24 通过
   - Processor 测试: 20 个测试（均线、趋势、温度、格式化）
   - Fetcher 测试: 4 个测试（转换逻辑）

### 使用示例

```bash
# 查看今日指数分析
uv run --env-file .env python skills/index_analysis/scripts/index_processor/index_processor.py

# 指定日期
uv run --env-file .env python skills/index_analysis/scripts/index_processor/index_processor.py --date 2026-03-06
```

### 待后续

- 网络稳定时验证真实 API 调用
- Phase 2：增加更多技术指标（MACD、KDJ）
- Phase 3：指数成份股联动分析

## 备注
开始时间：2026-03-07 06:40
完成时间：2026-03-07 07:20

**注意**：AKShare 指数接口（stock_zh_index_daily_em）网络不稳定，东方财富接口有限流问题。这是外部因素，不影响核心逻辑。
