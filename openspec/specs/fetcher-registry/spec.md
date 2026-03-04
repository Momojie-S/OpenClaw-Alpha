# FetcherRegistry 能力规格

## Purpose

FetcherRegistry 是全局单例注册表，管理所有 DataFetcher 实例的注册和查询。支持按名称索引、按数据类型分组查询，以及自动选择优先级最高的可用 Fetcher。

---

## Requirements

### Requirement: FetcherRegistry 是全局单例

系统 SHALL 确保 FetcherRegistry 在整个应用中只有一个实例。

#### Scenario: 多次获取返回同一实例
- **WHEN** 多次调用 `FetcherRegistry.get_instance()`
- **THEN** 系统返回同一个 FetcherRegistry 实例

### Requirement: Fetcher 注册

系统 SHALL 支持注册 DataFetcher 实例。

#### Scenario: 成功注册 Fetcher
- **WHEN** 调用 `registry.register(fetcher)`
- **THEN** 系统将该 Fetcher 添加到注册表，按 name 索引

#### Scenario: 注册重名 Fetcher 抛出异常
- **WHEN** 注册一个已存在名称的 Fetcher
- **THEN** 系统抛出 `DuplicateFetcherError` 异常

### Requirement: 按名称获取 Fetcher

系统 SHALL 支持按名称获取 DataFetcher 实例。

#### Scenario: 获取已注册的 Fetcher
- **WHEN** 调用 `registry.get("tushare_concept")`
- **THEN** 系统返回对应名称的 Fetcher 实例

#### Scenario: 获取未注册的 Fetcher 抛出异常
- **WHEN** 调用 `registry.get("unknown")` 获取未注册的 Fetcher
- **THEN** 系统抛出 `KeyError` 异常

### Requirement: 按数据类型获取所有 Fetcher

系统 SHALL 支持按 data_type 获取所有注册的 Fetcher。

#### Scenario: 获取同一类型的所有 Fetcher
- **WHEN** 调用 `registry.get_by_data_type("concept_board")`
- **THEN** 系统返回所有 data_type 为 "concept_board" 的 Fetcher 列表

#### Scenario: 获取不存在的类型返回空列表
- **WHEN** 调用 `registry.get_by_data_type("unknown_type")`
- **THEN** 系统返回空列表

### Requirement: 按数据类型获取可用的 Fetcher

系统 SHALL 支持按 data_type 获取所有可用的 Fetcher（数据源配置满足）。

#### Scenario: 获取可用的 Fetcher
- **WHEN** 调用 `registry.get_available("concept_board")`
- **THEN** 系统返回 data_type 为 "concept_board" 且 `is_available()` 为 True 的 Fetcher 列表

#### Scenario: 按优先级排序
- **WHEN** 获取可用 Fetcher 列表
- **THEN** 系统按 priority 降序排列（数值大的在前）

#### Scenario: 无可用 Fetcher 返回空列表
- **WHEN** 调用 `registry.get_available("concept_board")` 且该类型所有 Fetcher 的数据源都不可用
- **THEN** 系统返回空列表

### Requirement: FetcherRegistry 重置

系统 SHALL 支持重置注册表，用于测试场景。

#### Scenario: 重置清除所有注册
- **WHEN** 调用 `registry.reset()`
- **THEN** 系统清除所有已注册的 Fetcher
