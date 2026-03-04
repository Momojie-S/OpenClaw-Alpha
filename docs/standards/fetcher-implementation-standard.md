# DataFetcher 实现规范

## 设计目标

定义 DataFetcher 的实现规范，确保：
- 职责分离：API 调用与数据转换解耦
- 测试高效：只测转换逻辑，不测外部依赖
- 开发流程清晰：真实 API 调试，mock 测试
- 容错能力：自动重试机制处理临时故障

---

## 架构设计

### 职责分离原则

每个 DataFetcher 实现应分离 API 请求和数据转换。

**API 请求**（外部依赖）：
- 负责调用外部数据源接口
- 可能包含多个 API 调用
- 不适合自动化测试
- 需要添加自动重试机制

**数据转换**（业务逻辑）：
- 负责字段映射、格式转换、数据清洗
- 可能有多个转换步骤
- 需要充分测试
- 保持纯粹（无副作用，不依赖外部状态）

**原因**：
- API 调用涉及外部依赖，不稳定、慢
- 数据转换是核心业务逻辑，需要快速、可靠的测试
- 分离后可独立测试转换逻辑

### 方法命名

**命名灵活**：
- API 请求方法：`_call_api()`, `_fetch_xxx()`, `_query_yyy()` 等
- 数据转换方法：`_transform()`, `_parse_xxx()`, `_convert_yyy()` 等
- 方法数量根据实际需要决定（可以有多个）

### 关键属性

- `name`: Fetcher 唯一标识（格式：`{数据源}_{数据类型}`）
- `data_type`: 数据类型标识（用于分组）
- `required_data_source`: 数据源名称
- `priority`: 优先级（0-9，数值越大越优先）

---

## 自动重试机制

### 设计目标

API 请求容易遇到临时故障（限流、超时、网络问题），需要自动重试能力：
- 提高系统稳定性
- 减少人工干预
- 统一重试策略

### 实现方式

使用 **tenacity** 库，为 API 请求方法添加 `@retry` 装饰器。

### 默认重试策略

| 参数 | 值 | 说明 |
|------|---|------|
| `stop_after_attempt` | 3 | 最多重试 3 次 |
| `wait_exponential` | multiplier=1, min=1, max=30 | 指数退避：1s, 2s, 4s...最多 30s |
| `retry_if_exception_type` | 可重试异常 | 只重试特定异常 |

### 异常分类

#### 可重试异常

临时性故障，重试可能成功。

| 异常类 | 说明 | HTTP 状态码 |
|--------|------|-------------|
| `RateLimitError` | 请求过于频繁 | 429 |
| `TimeoutError` | 请求超时 | - |
| `ServerError` | 服务端错误 | 5xx |
| `NetworkError` | 网络连接问题 | - |

#### 不可重试异常

永久性故障，重试无法解决。

| 异常类 | 说明 | HTTP 状态码 |
|--------|------|-------------|
| `AuthenticationError` | 认证失败 | 401 |
| `PermissionError` | 权限不足 | 403 |
| `NotFoundError` | 资源不存在 | 404 |
| `ValidationError` | 参数错误 | 400 |

### 异常转换

API 请求方法需要将原始异常转换为可重试异常：
- 判断异常类型（限流、超时、服务端错误、网络错误）
- 抛出对应的可重试异常
- 其他异常不重试，直接抛出

---

## 开发流程

**核心流程**：开发 → 调试 → 编写测试

### 详细步骤

1. **实现 Fetcher** - 分离 API 请求和数据转换逻辑，提供 `__main__` 入口
2. **调试 API** - 直接运行 fetcher，确认 API 返回结构
3. **保存 Fixture** - 将真实响应保存为测试数据
4. **测试转换** - 用 fixture 测试数据转换方法
5. **运行测试** - 确保转换逻辑正确

**重要**：必须先调试 API，确认返回值满足预期，再编写测试。

### 调试方式

每个 Fetcher 应提供 `__main__` 入口，方便直接运行调试：

```bash
# 直接运行 fetcher 调试
uv run --env-file .env python -m openclaw_alpha.fetchers.concept_board.akshare

# 确认内容：
# - API 返回值结构
# - 字段名称和类型
# - 异常情况
```

**调试目的**：
- 了解真实 API 响应结构
- 发现字段映射问题
- 确认数据格式
- 保存为测试 fixture

---

## 测试规范

### 测试范围

**必须测试**：
- ✅ 数据转换逻辑（如 `_parse_xxx()`, `_transform_yyy()`, `_merge_data()`）
- ✅ 字段映射正确性
- ✅ 格式转换正确性
- ✅ 边界情况（空数据、缺失字段）

**不需要测试**：
- ❌ API 请求方法（如 `_call_api()`, `_fetch_xxx()`）
- ❌ 网络请求
- ❌ 第三方 SDK
- ❌ Fetcher 属性（name, priority 等）
- ❌ is_available() 等可用性检查
- ❌ 重试机制（由 tenacity 保证）

### 测试数量

每个 Fetcher 的转换测试 **3-5 个用例**：
1. 基本转换
2. 字段映射
3. 格式转换（如类型转换、去后缀）
4. 边界情况（1-2个）

### Mock 策略

- 数据转换方法通常是纯函数，直接用 fixture 数据
- 不需要 Mock API
- 如果需要测试 `fetch()` 方法，Mock API 请求方法返回 fixture

---

## 最佳实践

### API 请求方法设计

- 只负责调用 API，不做数据处理
- 返回原始 API 响应
- 添加 `@retry` 装饰器，配置重试策略
- 将原始异常转换为可重试异常

### 数据转换方法设计

- 无副作用
- 不依赖外部状态
- 输入确定则输出确定
- 可以有多个转换步骤

### 错误处理

- 在 `fetch()` 中统一处理异常
- 数据转换方法假设输入总是有效，让错误暴露问题

---

## 文件组织

```
src/openclaw_alpha/fetchers/
├── {data_type}/
│   ├── models.py              # 数据模型
│   ├── tushare.py             # Tushare 实现
│   └── akshare.py             # AKShare 实现

tests/fetchers/
├── {data_type}/
│   ├── test_tushare_transform.py
│   └── fixtures/
│       ├── tushare_response.json
│       └── akshare_response.json
```

---

## 参考资料

- [开发规范](development-standard.md)
- [策略框架设计](../architecture/strategy-framework.md)
