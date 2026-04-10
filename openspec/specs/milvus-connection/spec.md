# milvus-connection

Milvus 连接管理模块，提供单例客户端获取。

## Requirements

### Requirement: 获取 Milvus 客户端单例
模块 SHALL 提供 `get_client()` 函数，返回 `pymilvus.MilvusClient` 实例。多次调用 SHALL 返回同一实例。连接参数 SHALL 从 `settings.milvus_uri` 和 `settings.milvus_token` 获取。

#### Scenario: 首次调用创建连接
- **WHEN** 调用 `get_client()` 且之前未调用过
- **THEN** 从 `settings.milvus_uri` 和 `settings.milvus_token` 读取参数，创建 `pymilvus.MilvusClient` 实例并返回

#### Scenario: 后续调用返回同一实例
- **WHEN** 多次调用 `get_client()`
- **THEN** 每次返回的都是同一个 `pymilvus.MilvusClient` 实例

### Requirement: 配置缺失时报错
当必需的配置项未设置时，`get_client()` SHALL 抛出明确的错误信息。

#### Scenario: milvus_uri 缺失
- **WHEN** `settings.milvus_uri` 未配置，调用 `get_client()`
- **THEN** 抛出 `ValueError`，提示 `milvus_uri` 未配置

#### Scenario: milvus_token 缺失
- **WHEN** `settings.milvus_token` 未配置，调用 `get_client()`
- **THEN** 抛出 `ValueError`，提示 `milvus_token` 未配置

### Requirement: 关闭连接
模块 SHALL 提供 `close()` 函数，用于关闭 Milvus 连接并重置单例。

#### Scenario: 关闭后再次调用 get_client
- **WHEN** 调用 `close()` 后再调用 `get_client()`
- **THEN** 创建新的 `pymilvus.MilvusClient` 实例并返回
