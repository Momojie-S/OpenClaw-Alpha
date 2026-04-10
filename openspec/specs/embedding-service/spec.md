# embedding-service

Embedding 向量生成服务，工厂模式按环境变量自动选择实现。

## Requirements

### Requirement: Embedding 抽象接口
模块 SHALL 提供 `Embedder` 抽象基类，定义 `embed(text: str) -> list[float]` 接口。

### Requirement: 工厂函数获取 Embedder
模块 SHALL 提供 `get_embedder()` 函数，根据 `settings.dashscope_api_key` 自动选择实现并返回单例。

#### Scenario: DASHSCOPE_API_KEY 已配置
- **WHEN** `settings.dashscope_api_key` 已设置
- **THEN** 返回 `DashScopeEmbedder` 单例实例

#### Scenario: 无可用 API Key
- **WHEN** `settings.dashscope_api_key` 未配置
- **THEN** 抛出 `ValueError`

### Requirement: DashScope Embedding 实现
`DashScopeEmbedder` SHALL 调用百炼 text-embedding-v4 API，返回 1024 维向量。

#### Scenario: 正常调用
- **WHEN** 调用 `embed("测试文本")`
- **THEN** 返回长度为 1024 的 float 列表

#### Scenario: API 调用失败
- **WHEN** DashScope API 返回错误或超时
- **THEN** 抛出明确的异常
