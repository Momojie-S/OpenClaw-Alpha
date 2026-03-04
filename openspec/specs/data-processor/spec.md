# DataProcessor 能力规格

## Purpose

DataProcessor 是数据加工的抽象基类，组合多个 DataFetcher 获取数据并进行加工处理。Processor 只负责数据加工逻辑，不直接访问数据源，权限需求由组合的 Fetcher 自动计算（同类型 OR，不同类型 AND）。

---

## Requirements

### Requirement: DataProcessor 必须定义名称

系统 SHALL 要求 DataProcessor 子类定义唯一的名称属性。

#### Scenario: DataProcessor 提供名称
- **WHEN** 访问 DataProcessor 的 `name` 属性
- **THEN** 系统返回该 Processor 的唯一标识符字符串

### Requirement: DataProcessor 声明所需的 data_type 列表

系统 SHALL 要求 DataProcessor 声明需要的 data_type 列表。

#### Scenario: DataProcessor 提供所需数据类型
- **WHEN** 访问 DataProcessor 的 `required_data_types` 属性
- **THEN** 系统返回该 Processor 需要的 data_type 名称列表

### Requirement: DataProcessor 自动选择可用 Fetcher

系统 SHALL 在执行时为每个 data_type 自动选择优先级最高的可用 Fetcher。

#### Scenario: 为每个 data_type 选择 Fetcher
- **WHEN** DataProcessor 执行 `process()` 方法
- **THEN** 系统为 `required_data_types` 中的每个类型从 FetcherRegistry 获取可用的 Fetcher

#### Scenario: 优先选择高优先级 Fetcher
- **WHEN** 某个 data_type 有多个可用 Fetcher
- **THEN** 系统选择 priority 最高的 Fetcher

#### Scenario: 无可用 Fetcher 抛出异常
- **WHEN** 某个 data_type 没有可用的 Fetcher
- **THEN** 系统抛出 `NoAvailableFetcherError` 异常，包含 data_type 名称

### Requirement: DataProcessor 权限自动计算

系统 SHALL 根据 DataProcessor 组合的 Fetcher 自动计算权限需求。

#### Scenario: 同一 data_type 的多个 Fetcher 是 OR 关系
- **WHEN** 计算 Processor 权限需求
- **THEN** 同一 data_type 下所有 Fetcher 的数据源是 OR 关系（任一可用即可）

#### Scenario: 不同 data_type 之间是 AND 关系
- **WHEN** 计算 Processor 权限需求
- **THEN** 不同 data_type 的数据源要求是 AND 关系（所有类型都需要）

#### Scenario: 权限计算示例
- **WHEN** Processor 需要 concept_board 和 sw_industry
- **THEN** 权限为 (concept_board_fetchers 的数据源 OR) AND (sw_industry_fetchers 的数据源 OR)

### Requirement: DataProcessor 异步执行

系统 SHALL 要求 DataProcessor 的 `process()` 方法为异步方法。

#### Scenario: 执行 process 返回结果
- **WHEN** 调用 `await processor.process(params)`
- **THEN** 系统执行数据加工逻辑并返回指定类型的结果

### Requirement: DataProcessor 支持泛型

系统 SHALL 使用泛型支持不同 DataProcessor 的参数和返回类型。

#### Scenario: 类型安全参数和返回
- **WHEN** 定义 DataProcessor `class MyProcessor(DataProcessor[ProcessParams, ProcessResult])`
- **THEN** `process(params: ProcessParams)` 接受 `ProcessParams` 类型，返回 `ProcessResult` 类型

### Requirement: DataProcessor 不直接获取数据

系统 SHALL 要求 DataProcessor 不直接调用 DataSource，只能通过 Fetcher 获取数据。

#### Scenario: 通过 Fetcher 获取数据
- **WHEN** DataProcessor 需要数据
- **THEN** 系统必须通过 FetcherRegistry 获取 Fetcher 并调用其 fetch() 方法
