## ADDED Requirements

### Requirement: 策略声明数据源依赖

系统 SHALL 支持策略声明依赖的数据源名称列表，用于可用性检查。

#### Scenario: 策略提供数据源名称列表
- **WHEN** 访问策略的 `_data_source_names` 属性
- **THEN** 系统返回该策略依赖的数据源名称列表

### Requirement: 策略提供静态获取客户端方法

系统 SHALL 提供静态方法 `get_client(name)` 从注册表获取数据源客户端。

#### Scenario: 静态方法获取客户端
- **WHEN** 调用 `await Strategy.get_client("tushare")`
- **THEN** 系统从 DataSourceRegistry 获取对应数据源并返回其客户端

### Requirement: 策略异步执行

系统 SHALL 要求策略的 `run()` 方法为异步方法。

#### Scenario: 执行策略返回结果
- **WHEN** 调用 `await strategy.run(input)`
- **THEN** 系统执行策略逻辑并返回指定类型的结果

### Requirement: 策略支持泛型输入输出

系统 SHALL 使用泛型支持不同策略的输入输出类型。

#### Scenario: 类型安全输入输出
- **WHEN** 定义策略 `class MyStrategy(Strategy[str, Quote])`
- **THEN** `run(input: str)` 接受 `str` 类型，返回 `Quote` 类型

### Requirement: 策略入口注册实现

系统 SHALL 支持策略入口注册多个实现，按优先级管理。

#### Scenario: 注册实现
- **WHEN** 调用 `entry.register(impl, priority=1)`
- **THEN** 系统将实现及其优先级添加到实现列表

#### Scenario: 从实现读取数据源依赖
- **WHEN** 注册实现时
- **THEN** 系统自动从实现的 `_data_source_names` 读取数据源依赖

### Requirement: 策略入口自动选择实现

系统 SHALL 在执行时自动选择优先级最高且数据源可用的实现。

#### Scenario: 选择优先级最高的可用实现
- **WHEN** 调用 `await entry.run(input)` 且有多个实现可用
- **THEN** 系统选择优先级最高（数值最大）且所有数据源都可用的实现执行

#### Scenario: 跳过数据源不可用的实现
- **WHEN** 某个实现的数据源不可用
- **THEN** 系统跳过该实现，继续检查下一个

### Requirement: 无可用实现时抛出异常

系统 SHALL 在所有实现的数据源都不可用时抛出特定异常。

#### Scenario: 所有实现不可用抛出异常
- **WHEN** 调用 `await entry.run(input)` 且所有实现的数据源都不可用
- **THEN** 系统抛出 `NoAvailableImplementationError` 异常，包含策略名称和已检查的实现列表

### Requirement: 策略入口继承策略基类

系统 SHALL 让 StrategyEntry 继承 Strategy，保持统一接口。

#### Scenario: 入口也是策略
- **WHEN** 检查 StrategyEntry 是否为 Strategy 的子类
- **THEN** 系统返回 `True`
