# DataFetcher 实现规范

## 数据获取策略

### 优先级

| 优先级 | 方式 | 说明 |
|:------:|------|------|
| 1 | 官方 API（免费可用） | 稳定、合规，优先使用 |
| 2 | RSS/Atom | 结构化、轻量 |
| 3 | web_fetch | 静态页面，简单场景 |
| 4 | browser | 需要 JS 渲染或有反爬 |
| 5 | curl | web_fetch 不够灵活时 |

### 不做

- ❌ **web_search** - 这是大模型能力，不是 Fetcher 职责
- ❌ **Python 爬虫** - 维护成本高，不稳定，容易违规

### 遇到需要认证/付费的 API

1. 在 `docs/references/api/` 下新建子目录（按服务提供商命名）
2. 记录 API 信息（地址、功能、价格、认证方式）
3. **暂不使用**，继续寻找替代方案

---

## 设计目标

- **职责单一**：只负责数据获取，不做业务加工
- **职责分离**：API 调用与数据转换解耦
- **测试高效**：只测转换逻辑，不测外部依赖
- **容错能力**：自动重试机制处理临时故障

---

## 架构设计

### 职责分离

| 层次 | 职责 | 特点 |
|------|------|------|
| API 请求 | 调用外部接口 | 外部依赖，不稳定 |
| 数据转换 | 字段映射、格式转换 | 纯函数，可测试 |

**分离原因**：API 调用不稳定、慢，数据转换是核心逻辑，需要快速可靠的测试。

### 方法命名

- API 请求：`_call_api()`, `_fetch_xxx()`, `_query_yyy()`
- 数据转换：`_transform()`, `_parse_xxx()`, `_convert_yyy()`

### 关键属性

**Fetcher（入口类）**：`name` - Fetcher 标识

**FetchMethod（实现类）**：
- `name` - Method 标识
- `required_data_source` - 需要的数据源名称
- `required_credit` - 需要的积分（仅 Tushare）
- `priority` - 优先级（数值越大越优先）

### 积分校验

Tushare 数据源有积分要求，通过 `required_credit` 声明。

**校验流程**：
1. `FetchMethod.is_available()` 检查 token + 积分
2. 校验失败返回 `(False, error)`
3. Fetcher 收集所有失败原因，全部失败时抛出 `NoAvailableMethodError`

**异常类型**：
- `DataSourceUnavailableError` - 数据源不可用基类
- `MissingConfigError` - 配置缺失（token 等）
- `InsufficientCreditError` - 积分不足

---

## 自动重试机制

使用 **tenacity** 库，为 API 请求方法添加 `@retry` 装饰器。

**默认策略**：
- 最多重试 3 次
- 指数退避：1s, 2s, 4s...最多 30s
- 只重试可重试异常

**异常分类**：

| 可重试 | 不可重试 |
|--------|----------|
| `RateLimitError` (429) | `AuthenticationError` (401) |
| `TimeoutError` | `PermissionError` (403) |
| `ServerError` (5xx) | `NotFoundError` (404) |
| `NetworkError` | `ValidationError` (400) |

---

## 开发流程

1. **实现 Fetcher** - 分离 API 请求和数据转换，提供 `__main__` 入口
2. **调试 API** - 直接运行 fetcher，确认 API 返回结构
3. **保存 Fixture** - 将真实响应保存为测试数据
4. **测试转换** - 用 fixture 测试数据转换方法
5. **运行测试** - 确保转换逻辑正确

**重要**：必须先调试 API，确认返回值满足预期，再编写测试。

---

## 测试规范

### 测试范围

| 必须测试 | 不需要测试 |
|----------|-----------|
| 数据转换逻辑 | API 请求方法 |
| 字段映射 | 网络请求 |
| 格式转换 | 第三方 SDK |
| 边界情况 | Method 属性、可用性检查、重试机制 |

### 测试数量

每个 Fetcher 的转换测试 **3-5 个用例**：
1. 基本转换
2. 字段映射
3. 格式转换
4. 边界情况（1-2个）

---

## 最佳实践

### API 请求方法

- 只负责调用 API，不做数据处理
- 返回原始 API 响应
- 添加 `@retry` 装饰器
- 将原始异常转换为可重试异常

### 数据转换方法

- 无副作用，不依赖外部状态
- 输入确定则输出确定
- 可以有多个转换步骤

### 错误处理

- 在 `fetch()` 中统一处理异常
- 数据转换方法假设输入总是有效

### 参数处理

**必需参数校验**：
- 某些 API 要求特定参数组合（如 Tushare forecast 接口要求 `ann_date` 或 `ts_code`）
- 在 `_call_api()` 中正确处理参数映射（如 `date` → `ann_date`）
- 提供清晰的错误提示，告知用户缺少哪些必需参数

**调用链参数传递**：
- Processor → `fetch()` → Fetcher → `FetchMethod.fetch()`
- 每一层都需要正确传递参数
- 确保参数命名一致（统一使用 `date`、`symbol`，在 FetchMethod 内部转换为 API 所需格式）

**股票代码格式转换**：
- 内部统一使用 6 位代码（如 `000001`）
- FetchMethod 内部转换为数据源所需格式
- 转换规则（Tushare/AKShare）：
  - `60*`, `68*` → 上交所 `.SH`
  - `00*`, `30*` → 深交所 `.SZ`
  - `688*`, `689*` → 科创板 `.SH`
- 参考策略框架的"数据格式约定"

---

## 参考资料

- [开发规范](development-standard.md) - Python 编码、测试规范
- [Skill 实现规范](skill-implementation-standard.md) - 目录结构、命名规范、运行方式
- [策略框架设计](../architecture/strategy-framework.md) - 架构设计
