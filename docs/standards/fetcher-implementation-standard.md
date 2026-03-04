# DataFetcher 实现规范

> 版本: v1.0
> 创建时间: 2026-03-04

---

## 设计目标

定义 DataFetcher 的实现规范，确保：
- 职责分离：API 调用与数据转换解耦
- 测试高效：只测转换逻辑，不测外部依赖
- 开发流程清晰：真实 API 调试，mock 测试

---

## 架构设计

### 职责分离

每个 DataFetcher 应分离 API 调用和数据转换：

```
fetch() - 入口方法
├── _call_api() - API 调用（外部依赖）
└── _transform() - 数据转换（业务逻辑）
```

**原因**：
- API 调用涉及外部依赖，不适合自动化测试
- 数据转换是业务逻辑，需要充分测试
- 分离后可独立测试转换逻辑

### 关键属性

- `name`: Fetcher 唯一标识（格式：`{数据源}_{数据类型}`）
- `data_type`: 数据类型标识（用于分组）
- `required_data_source`: 数据源名称
- `priority`: 优先级（0-9，数值越大越优先）

---

## 开发流程

### 流程步骤

1. **实现 Fetcher** - 分离 `_call_api()` 和 `_transform()`
2. **调试 API** - 用独立脚本调用真实 API，确认返回结构
3. **保存 Fixture** - 将真实响应保存为测试数据
4. **测试转换** - 用 fixture 测试 `_transform()`
5. **运行测试** - 确保转换逻辑正确

### 调试 API

使用独立脚本调用真实 API：

```bash
# 运行调试脚本
uv run --env-file .env python scripts/debug_tushare_concept.py

# 确认内容：
# - API 返回值结构
# - 字段名称和类型
# - 异常情况
```

---

## 测试规范

### 测试范围

**必须测试**：
- ✅ 数据转换逻辑（`_transform()`）
- ✅ 字段映射正确性
- ✅ 格式转换正确性
- ✅ 边界情况（空数据、缺失字段）

**不需要测试**：
- ❌ API 调用（`_call_api()`）
- ❌ 网络请求
- ❌ 第三方 SDK

### 测试数量

每个 Fetcher 的转换测试 **3-5 个用例**：
1. 基本转换
2. 字段映射
3. 格式转换（如去后缀）
4. 边界情况（1-2个）

### Mock 策略

- 转换函数 `_transform()` 是纯函数，直接用 fixture 数据
- 不需要 Mock API
- 如果需要测试 `fetch()` 方法，Mock `_call_api()` 返回 fixture

---

## 最佳实践

### 转换函数设计

**保持纯粹**：
- 无副作用
- 不依赖外部状态
- 输入确定则输出确定

### 错误处理

- 在 `fetch()` 中处理异常
- `_transform()` 假设输入总是有效，让错误暴露问题

### 日志记录

- 在 `fetch()` 中记录
- 不在 `_transform()` 中记录

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

scripts/
└── debug_{data_source}_{data_type}.py
```

---

## 参考资料

- [开发规范](development-standard.md)
- [策略框架设计](../architecture/strategy-framework.md)
