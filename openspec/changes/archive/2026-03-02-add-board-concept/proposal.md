## Why

当前项目已有行业板块行情查询功能（board_industry.py），但缺少概念板块行情查询能力。概念板块（如"人工智能"、"新能源汽车"等）是 A 股市场重要的分析维度，用户需要获取概念板块的实时行情数据进行分析。

## What Changes

- 新增概念板块行情查询脚本 `src/openclaw_alpha/commands/board_concept.py`
- 新增子 skill `skills/board-concept/SKILL.md`
- 复用 `board_industry.py` 的架构模式，使用 AKShare 的 `stock_board_concept_name_em()` 接口

## Capabilities

### New Capabilities

- `board-concept-query`: A 股概念板块实时行情查询能力，支持排序和筛选

### Modified Capabilities

无

## Impact

- 新增代码文件，不影响现有功能
- 数据源：东方财富（通过 AKShare），无需认证
