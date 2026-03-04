# DataFetcher 能力规格

## Purpose

DataFetcher 是数据获取的抽象基类，定义了从特定数据源获取特定类型数据的标准接口。每个 Fetcher 实现对应一个数据源的一种数据类型获取逻辑，支持优先级排序和可用性检查。

---

## Requirements

### Requirement: DataFetcher 必须定义名称

系统 SHALL 要求 DataFetcher 子类定义唯一的名称属性，用于注册表索引。

#### Scenario: DataFetcher 提供名称
- **WHEN** 访问 DataFetcher 的 `name` 属性
- **THEN** 系统返回该 Fetcher 的唯一标识符字符串

### Requirement: DataFetcher 必须定义数据类型

系统 SHALL 要求 DataFetcher 子类定义 data_type 属性，用于分组和权限计算。

#### Scenario: DataFetcher 提供数据类型
- **WHEN** 访问 DataFetcher 的 `data_type` 属性
- **THEN** 系统返回该 Fetcher 获取的数据类型标识符

### Requirement: DataFetcher 声明单一数据源

系统 SHALL 要求 DataFetcher 声明依赖的单一数据源名称。

#### Scenario: DataFetcher 提供数据源名称
- **WHEN** 访问 DataFetcher 的 `required_data_source` 属性
- **THEN** 系统返回该 Fetcher 依赖的数据源名称字符串

#### Scenario: 一个 Fetcher 只依赖一个数据源
- **WHEN** 定义 DataFetcher 子类
- **THEN** `required_data_source` 必须是单一数据源名称，而非列表

### Requirement: DataFetcher 支持优先级

系统 SHALL 支持 DataFetcher 定义优先级，用于同类型多个实现的选择。

#### Scenario: DataFetcher 提供优先级
- **WHEN** 访问 DataFetcher 的 `priority` 属性
- **THEN** 系统返回该 Fetcher 的优先级数值（默认为 0）

#### Scenario: 优先级数值越大越优先
- **WHEN** 同一 data_type 有多个可用 Fetcher
- **THEN** 系统优先选择 priority 数值最大的实现

### Requirement: DataFetcher 异步获取数据

系统 SHALL 要求 DataFetcher 的 `fetch()` 方法为异步方法。

#### Scenario: 执行 fetch 返回数据
- **WHEN** 调用 `await fetcher.fetch(params)`
- **THEN** 系统执行数据获取逻辑并返回指定类型的结果

### Requirement: DataFetcher 支持泛型

系统 SHALL 使用泛型支持不同 DataFetcher 的参数和返回类型。

#### Scenario: 类型安全参数和返回
- **WHEN** 定义 DataFetcher `class MyFetcher(DataFetcher[FetchParams, FetchResult])`
- **THEN** `fetch(params: FetchParams)` 接受 `FetchParams` 类型，返回 `FetchResult` 类型

### Requirement: DataFetcher 检查数据源可用性

系统 SHALL 支持 DataFetcher 检查其数据源是否可用。

#### Scenario: 数据源可用返回 True
- **WHEN** 调用 `fetcher.is_available()` 且其 `required_data_source` 对应的数据源配置满足
- **THEN** 系统返回 `True`

#### Scenario: 数据源不可用返回 False
- **WHEN** 调用 `fetcher.is_available()` 且其 `required_data_source` 对应的数据源配置不满足
- **THEN** 系统返回 `False`

### Requirement: DataFetcher API 请求方法支持自动重试

DataFetcher 的 API 请求方法 SHALL 使用 `@retry` 装饰器实现自动重试能力。

#### Scenario: API 请求方法使用重试装饰器
- **WHEN** 定义 DataFetcher 的 API 请求方法（如 `_call_api()`、`_fetch_xxx()`）
- **THEN** 该方法使用 `@retry` 装饰器配置重试策略

#### Scenario: 重试只应用于 API 请求方法
- **WHEN** 定义数据转换方法（如 `_transform()`、`_parse_xxx()`）
- **THEN** 该方法不使用重试装饰器

### Requirement: DataFetcher 区分 API 请求和数据转换职责

DataFetcher 的 API 请求方法 SHALL 只负责调用外部 API，不做数据处理；数据转换方法 SHALL 不依赖外部状态。

#### Scenario: API 请求方法返回原始响应
- **WHEN** 调用 API 请求方法
- **THEN** 方法返回原始 API 响应，不做字段映射或格式转换

#### Scenario: 数据转换方法是纯函数
- **WHEN** 调用数据转换方法
- **THEN** 相同输入总是产生相同输出，无副作用
