## Context

当前 Strategy 基类同时承担两种职责：
- **获取数据**：调用数据源 API，处理原始数据格式
- **加工数据**：组合多个数据，计算指标，生成业务结果

这导致权限声明不精确（无法表达「A 或 B」）、组合困难、复用性差。

现有代码结构：
- `core/strategy.py` - Strategy 基类和 StrategyEntry
- `core/registry.py` - DataSourceRegistry
- `core/data_source.py` - DataSource 基类
- `commands/board_concept.py` - 使用 Strategy 的命令实现
- `commands/sw_industry.py` - 使用 Strategy 的命令实现

## Goals / Non-Goals

**Goals:**
- 分离数据获取和数据加工职责
- 权限需求可自动计算（按 data_type 分组，组内 OR，组间 AND）
- 数据获取逻辑可复用
- 保持向后兼容，现有 Strategy 代码可继续使用

**Non-Goals:**
- 不修改 DataSource 和 DataSourceRegistry
- 不一次性迁移所有现有实现
- 不支持跨数据源的事务性操作

## Decisions

### D1: DataFetcher 职责定义

**决定**: DataFetcher 只负责获取某一类数据，一个实现只用一种数据源。

**关键属性**:
- `name` - Fetcher 标识，如 `tushare_concept`
- `data_type` - 数据类型，如 `concept_board`（用于分组和 OR 关系）
- `required_data_source` - 需要的数据源名称（单一数据源）
- `priority` - 优先级（数值越大越优先）

**备选方案**: 允许一个 Fetcher 使用多个数据源
- **拒绝原因**: 会导致权限声明复杂化，失去分组 OR 的简洁性

### D2: DataProcessor 职责定义

**决定**: DataProcessor 组合多个 Fetcher，只做数据加工，不直接获取数据。

**权限计算规则**:
1. 按 data_type 分组
2. 同组内多个 Fetcher 是 OR 关系（任一可用即可）
3. 不同组之间是 AND 关系（所有组都需要）

**备选方案**: Processor 显式声明需要的数据源
- **拒绝原因**: 无法表达「A 或 B」的语义，且与 Fetcher 声明重复

### D3: FetcherRegistry 设计

**决定**: 新增 FetcherRegistry 管理所有 Fetcher 实例。

**关键方法**:
- `register(fetcher)` - 注册 Fetcher
- `get(name)` - 按名称获取
- `get_by_data_type(data_type)` - 按数据类型获取所有实现
- `get_available(data_type)` - 获取数据类型下所有可用的 Fetcher（数据源配置满足）

**备选方案**: 复用 DataSourceRegistry
- **拒绝原因**: 两者职责不同，DataSource 管理连接，Fetcher 管理数据获取逻辑

### D4: 数据关联策略

**决定**: 用 `name` 关联，不用 `code`。

**原因**:
- 名称在不同数据源间更稳定
- 简单直接，无需处理代码格式转换（如 `000001.SZ` vs `000001`）

**风险**: 名称可能存在细微差异
- **缓解**: 板块/股票名称重复和变更概率很低，可接受

### D5: 目录结构

**决定**:
- `fetchers/<data_type>/<source>.py` - Fetcher 按 data_type 组织
- `processors/<business>/processor.py` - Processor 按业务场景组织

**原因**: 同一 data_type 的多个实现放在一起，便于管理和选择

## Risks / Trade-offs

### R1: 迁移成本
- **风险**: 现有实现需要逐步迁移
- **缓解**: 保留 Strategy 基类，新功能用 Fetcher + Processor，渐进式迁移

### R2: 概念复杂度
- **风险**: 引入新概念增加学习成本
- **缓解**: 职责分离后更清晰，长远看降低理解成本

### R3: 名称关联可能失败
- **风险**: 不同数据源的名称可能有细微差异
- **缓解**: 在 Fetcher 中做名称标准化，或接受轻微差异
