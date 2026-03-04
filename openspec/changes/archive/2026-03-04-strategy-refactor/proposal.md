## Why

当前 Strategy 基类同时承担「获取数据」和「加工数据」两种职责，导致三个问题：

1. **权限声明不精确** - 策略需要多个数据源时，无法表达「数据 A 可从 Tushare 或 AKShare 获取」的语义
2. **组合困难** - 复杂策略组合多个数据源时，权限检查和降级逻辑分散在各处
3. **复用性差** - 同一个数据获取逻辑（如概念板块行情）在不同策略中重复实现

通过职责分离，使权限需求可自动计算、数据获取逻辑可复用。

## What Changes

- **新增 DataFetcher 基类** - 专门负责数据获取，一个实现只用一种数据源
- **新增 DataProcessor 基类** - 组合多个 Fetcher，只做数据加工
- **新增 FetcherRegistry** - 管理所有 Fetcher 实例，支持按 data_type 查询
- ****BREAKING** 重构现有 strategy 实现** - 将 `board_concept` 和 `sw_industry` 迁移到 Fetcher + Processor 架构
- **保留 Strategy 基类** - 兼容现有代码，后续逐步迁移

## Capabilities

### New Capabilities

- `data-fetcher`: 数据获取器基类，声明单一数据源权限，按 data_type 分组
- `fetcher-registry`: Fetcher 注册表，按 data_type 查询可用实现，支持优先级排序
- `data-processor`: 数据加工器基类，组合多个 Fetcher，权限自动推导

### Modified Capabilities

- `strategy`: 现有 Strategy 将逐步迁移到新架构，保留向后兼容

## Impact

- **新增模块**: `core/fetcher.py`, `core/processor.py`, `core/fetcher_registry.py`
- **新增目录**: `fetchers/`, `processors/`
- **迁移影响**: `commands/board_concept.py`, `commands/sw_industry.py`
- **文档更新**: `docs/architecture/strategy-framework.md` 合并新设计
