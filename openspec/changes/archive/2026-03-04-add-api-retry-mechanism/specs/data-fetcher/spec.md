## ADDED Requirements

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
