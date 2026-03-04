## ADDED Requirements

### Requirement: 系统定义可重试异常类型

系统 SHALL 定义以下可重试异常类，用于标识临时性故障：
- RateLimitError：请求频率超限（HTTP 429）
- TimeoutError：请求超时
- ServerError：服务端错误（HTTP 5xx）
- NetworkError：网络连接问题

#### Scenario: 可重试异常触发重试
- **WHEN** API 请求抛出 RateLimitError、TimeoutError、ServerError 或 NetworkError
- **THEN** 系统自动重试该请求

#### Scenario: 可重试异常继承关系
- **WHEN** 定义可重试异常类
- **THEN** 所有可重试异常继承自共同的基类 `RetryableError`

### Requirement: 系统定义不可重试异常类型

系统 SHALL 定义以下不可重试异常类，用于标识永久性故障：
- AuthenticationError：认证失败（HTTP 401）
- PermissionError：权限不足（HTTP 403）
- NotFoundError：资源不存在（HTTP 404）
- ValidationError：参数验证失败（HTTP 400）

#### Scenario: 不可重试异常不触发重试
- **WHEN** API 请求抛出 AuthenticationError、PermissionError、NotFoundError 或 ValidationError
- **THEN** 系统立即抛出异常，不进行重试

### Requirement: 重试使用指数退避策略

系统 SHALL 使用指数退避策略进行重试，参数如下：
- 最大重试次数：3 次
- 初始等待时间：1 秒
- 等待时间倍数：2
- 最大等待时间：30 秒

#### Scenario: 指数退避序列
- **WHEN** API 请求第一次失败
- **THEN** 等待 1 秒后重试
- **AND** 第二次失败后等待 2 秒
- **AND** 第三次失败后等待 4 秒

#### Scenario: 最大等待时间限制
- **WHEN** 计算出的等待时间超过 30 秒
- **THEN** 实际等待时间为 30 秒

### Requirement: API 请求方法必须转换异常

API 请求方法 SHALL 将第三方库的原始异常转换为系统定义的可重试异常或不可重试异常。

#### Scenario: 限流异常转换
- **WHEN** 第三方 SDK 返回限流错误（如 HTTP 429）
- **THEN** API 请求方法抛出 RateLimitError

#### Scenario: 超时异常转换
- **WHEN** 第三方 SDK 返回超时错误
- **THEN** API 请求方法抛出 TimeoutError

#### Scenario: 服务端异常转换
- **WHEN** 第三方 SDK 返回服务端错误（HTTP 5xx）
- **THEN** API 请求方法抛出 ServerError

#### Scenario: 网络异常转换
- **WHEN** 第三方 SDK 返回网络连接错误
- **THEN** API 请求方法抛出 NetworkError

#### Scenario: 其他异常不重试
- **WHEN** API 请求遇到未分类的异常
- **THEN** 直接抛出原始异常，不触发重试
