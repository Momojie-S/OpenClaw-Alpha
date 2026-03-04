## Why

API 请求容易遇到临时故障（限流、超时、网络问题），目前 DataFetcher 实现缺乏自动重试能力，导致偶发性的请求失败需要人工干预。添加自动重试机制可以提高系统稳定性和可靠性。

## What Changes

- 添加 tenacity 依赖作为重试库
- 新增可重试异常类：RateLimitError、TimeoutError、ServerError、NetworkError
- 为 API 请求方法提供统一的 `@retry` 装饰器配置
- 更新现有 Fetcher 实现，为 API 请求方法添加重试支持

## Capabilities

### New Capabilities

- `api-retry`: API 请求自动重试能力，包括异常分类、重试策略配置

### Modified Capabilities

- `data-fetcher`: 基类增加重试相关支持，更新规范文档中已描述但未实现的重试机制

## Impact

- `pyproject.toml`: 添加 tenacity 依赖
- `src/openclaw_alpha/core/exceptions.py`: 新增可重试异常类
- `src/openclaw_alpha/fetchers/`: 所有 Fetcher 实现需要为 API 请求方法添加 `@retry` 装饰器
- `docs/standards/fetcher-implementation-standard.md`: 已包含重试机制设计，无需修改
