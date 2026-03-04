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

### 职责分离原则

每个 DataFetcher 实现应分离 API 请求和数据转换：

**API 请求**（外部依赖）：
- 负责调用外部数据源接口
- 可能包含多个 API 调用（如：先获取列表，再获取详情）
- 不适合自动化测试

**数据转换**（业务逻辑）：
- 负责字段映射、格式转换、数据清洗
- 可能有多个转换步骤（如：解析原始数据、合并多个数据源）
- 需要充分测试

**原因**：
- API 调用涉及外部依赖，不稳定、慢
- 数据转换是核心业务逻辑，需要快速、可靠的测试
- 分离后可独立测试转换逻辑

### 实现建议

**命名灵活**：
- API 请求方法：`_call_api()`, `_fetch_xxx()`, `_query_yyy()` 等
- 数据转换方法：`_transform()`, `_parse_xxx()`, `_convert_yyy()` 等
- 方法数量根据实际需要决定（可以有多个）

**示例结构**：
```
fetch() - 入口方法
├── _fetch_list() - 获取列表数据（API 请求）
├── _fetch_detail() - 获取详情数据（API 请求）
├── _parse_list() - 解析列表（数据转换）
└── _merge_data() - 合并数据（数据转换）
```

### 关键属性

- `name`: Fetcher 唯一标识（格式：`{数据源}_{数据类型}`）
- `data_type`: 数据类型标识（用于分组）
- `required_data_source`: 数据源名称
- `priority`: 优先级（0-9，数值越大越优先）

---

## 开发流程

**核心流程**：开发 → 调试 → 编写测试

### 详细步骤

1. **实现 Fetcher** - 分离 API 请求和数据转换逻辑
2. **调试 API** - 用独立脚本调用真实 API，确认返回结构
3. **保存 Fixture** - 将真实响应保存为测试数据
4. **测试转换** - 用 fixture 测试数据转换方法
5. **运行测试** - 确保转换逻辑正确

**重要**：必须先调试 API，确认返回值满足预期，再编写测试。

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

**职责单一**：
- 只负责调用 API，不做数据处理
- 返回原始 API 响应
- 异常处理：捕获 API 错误，抛出统一异常

### 数据转换方法设计

**保持纯粹**：
- 无副作用
- 不依赖外部状态
- 输入确定则输出确定
- 可以有多个转换步骤

**示例**：
```python
def _parse_list(self, raw_data: dict) -> list[Item]:
    """解析列表数据"""
    # 纯函数：输入原始数据，输出结构化数据
    pass

def _merge_data(self, list_data: list, detail_data: dict) -> Result:
    """合并多个数据源"""
    # 纯函数：不依赖外部状态
    pass
```

### 错误处理

- 在 `fetch()` 中统一处理异常
- 数据转换方法假设输入总是有效，让错误暴露问题

### 日志记录

- 在 `fetch()` 中记录关键步骤
- 不在转换方法中记录（保持纯粹）

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
