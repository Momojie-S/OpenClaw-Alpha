# 开发规范

## 开发前准备

开始开发前，请确保已配置标准开发环境（Python、uv 等），并安装项目特定的开发工具，详见 [development-environment.md](development-environment.md)。

## 技术约束

- **算力有限，不涉及机器学习**：量化模型、ML 预测、深度学习等均不考虑
- 优先采用规则驱动、统计指标等轻量方案

## API 调用验证规范

**所有涉及外部 API 调用的代码，必须遵循以下流程**：

1. **编写代码后必须实际调用 API**，获取真实结果
2. **跑通完整流程**，确认返回结构、参数传递、异常处理都正确
3. **验证通过后**，才能进入测试阶段

**禁止**：写完代码直接写测试，跳过实际调用验证

**原因**：
- API 返回结构可能与文档不一致
- 需要验证参数传递、异常处理是否正确
- 确保数据转换逻辑基于真实数据设计

**适用范围**：
- Fetcher（数据获取）
- Processor（如涉及 API 调用）
- 任何调用外部服务的代码

## Python 开发规范

### 编码规范
- **异步优先**: 所有操作均使用 async/await
- **文档注释**: 所有函数必须具有 Google 风格的文档注释，代码中也需要对必要逻辑加入注释说明。所有的注释都必须使用中文编写
- **类型提示**: 所有类成员变量和函数签名必须包含类型提示 (Type Hinting)
- **内置泛型**: 使用内置泛型类型（`list`, `dict`）而不是从 `typing` 模块导入（`List`, `Dict`）
- **导入规范**:
  - **基类导入**: 使用绝对路径导入框架基类，如 `from openclaw_alpha.core.fetcher import Fetcher`
  - **Skill 内部导入**: 使用相对路径导入，如 `from .xxx import xxx` 或 `from ..xxx import xxx`
  - **类型注解导入**: 仅用于类型注解的导入应使用 `TYPE_CHECKING`
- **父类构造函数**: 在所有子类的 `__init__` 方法中，调用父类构造函数时必须显式传入所有必需参数
  - 允许使用 `super().__init__(...)`，但必须确保所有参数都显式传递
  - 示例：`super().__init__(arg1=value1, arg2=value2)` 而非依赖默认参数隐式传递
- **显式数据结构**: 应该定义一个对象，而不是使用 dict。必须适应类定义字段，不能使用 `getattr` 和 `setattr`
- **模块命名**: Python 模块和目录名必须使用下划线 `_`（如 `industry_trend`），不能使用连字符 `-`（如 `industry-trend`），否则会导致导入失败
- **模块暴露**: 没有收到指示的情况下，不要在 `__init__.py` 中新增暴露任何模块
- **编码声明**: 所有 Python 文件必须在文件开头添加 UTF-8 编码声明：`# -*- coding: utf-8 -*-`
- **禁止特殊字符**: 禁止在代码中使用表情符号和特殊 Unicode 符号（如 emoji、数学符号等），保持代码可读性和兼容性
- **日志模块**: 统一使用 `logging` 模块获取日志对象
- **MySQL**: 优先使用 ORM 进行 MySQL 相关查询
- **异常处理**: 所有抛出的异常或返回的错误信息必须包含三个要素：
  1. **问题来源**：明确指出是哪方的责任（用户配置、代码bug、第三方服务、数据问题等）
  2. **用户能否解决**：告知用户这个问题是否在他们的控制范围内
  3. **解决方案**：如果能解决，提供具体的解决步骤或建议

  **异常分类与模板**：

  | 问题类型 | 问题来源 | 用户能否解决 | 信息模板 |
  |---------|---------|------------|----------|
  | 配置缺失 | 用户 | ✅ 能 | "缺少 {配置项} 配置。请在 .env 文件中添加：{配置项}={说明}。获取方式：{URL}" |
  | 积分不足 | 用户 | ✅ 能 | "{服务} 积分不足（当前 {当前值}，需要 {需要值}）。请登录 {URL} 充值积分" |
  | 参数错误 | 用户 | ✅ 能 | "参数 {参数名} {错误原因}（收到 '{实际值}'，{期望说明}）。{正确用法示例}" |
  | 数据不存在 | 用户/数据源 | ✅ 能 | "{数据类型} {标识} 不存在。请检查{检查项}是否正确" |
  | 网络超时 | 第三方 | ✅ 能（重试） | "连接 {服务} API 超时。请检查网络连接后重试" |
  | API 限流 | 第三方 | ✅ 能（等待） | "{服务} API 请求频率超限（{限制说明}）。请等待 {时间} 后重试" |
  | 代码错误 | 开发者 | ❌ 不能 | "内部错误：{操作} 时发生异常。这是代码 bug，请联系开发者并提供：错误日志、使用参数、触发时间" |
  | 第三方服务故障 | 第三方 | ❌ 不能（临时） | "{服务} API 服务不可用（HTTP {状态码}）。请稍后重试，若持续失败请联系开发者" |

  **实践要点**：
  - 使用自定义异常类（如 `MissingConfigError`、`InsufficientCreditError`）而非通用异常
  - 错误信息面向用户，而非开发者（代码 bug 除外）
  - 包含必要的上下文信息（如当前值、期望值、获取方式等）
  - 提供 URL 链接，方便用户快速找到解决方案
  - 代码 bug 类异常要记录完整日志（`exc_info=True`）

### 依赖管理

- **添加依赖**: 优先使用 `uv add <package>` 命令
  - 会自动更新 `pyproject.toml` 和 `uv.lock`
  - 示例：`uv add numpy`
- **添加开发依赖**: 使用 `uv add --dev <package>`
  - 示例：`uv add --dev pytest`
- **特殊情况**: 如果 `uv add` 无法正常工作，再使用 `uv pip install <package>`
- **禁止**: 不要直接手动修改 `pyproject.toml` 的 dependencies 字段

### 测试规范

- **无测试包**: 不得在测试目录中创建 python package
- **测试类和 Fixtures**: 测试文件必须使用测试类（以 `Test` 为前缀）来组织相关的测试方法。必须使用 `pytest.fixture` 来管理测试依赖和状态
- **测试文件命名**: 避免在不同目录使用相同的测试文件名（如多个 `test_processor.py`），会导致 Python 模块导入冲突。应使用具描述性的唯一名称（如 `test_sentiment_processor.py`, `test_risk_processor.py`）
- **单例模式测试**: 测试涉及单例模式（如 DataSourceRegistry）时，必须在测试前重置状态，避免测试间干扰。可在 conftest.py 中使用 autouse fixture 进行重置
- **fixture 复用**: 通用 fixture（如临时目录、mock 配置等）应在 `conftest.py` 中定义，避免重复代码
- **导入约定**: 由于项目使用 `src-layout`，测试文件中的导入路径不得包含 `src` 目录
  - 正确：`from openclaw_alpha.core.agent import Agent`
  - 错误：`from src.openclaw_alpha.core.agent import Agent`
- **运行测试**: 运行测试时必须使用 `uv run --env-file .env pytest ...`，因为环境变量中包含 `PYTHONPATH` 指向 src 目录
- **按功能组组织测试**: 测试文件应按功能相关性组织。对于特别复杂的方法，可以单独创建测试文件；简单方法应合并到相关功能组的测试文件中
- **异步测试装饰器**: 所有异步测试方法必须同时包含 `@pytest.mark.asyncio` 和 `@pytest.mark.timeout` 装饰器
- **Mock 路径规则**: Mock 时 patch 模块被导入的位置，而非定义位置。例如：`patch("openclaw_alpha.fetchers.concept_board.akshare.ak.stock_board_concept_name_em")` 而非 `patch("ak.stock_board_concept_name_em")`
- **临时文件**: 使用当前工作目录下的 `.temp` 目录来存储临时文件
- **保证逻辑正确**: 除非源代码逻辑有错误，否则不能因为测试不通过而修改源代码
- **诚实原则**: 当测试用例失败且不知道原因或如何修复时，应停下来询问下一步该怎么做
- **测试数据清理**: 测试产生的数据必须在测试完成后清理
  - 使用 pytest fixture 的 `yield` 和 `finalizer` 机制确保测试后清理
  - 测试数据必须使用 `test_` 前缀标记（如 id 为 `test_user_123` 或 name 为 `test_session_abc`），便于识别和清理
- **大模型选用**: 测试时如果需要使用真实的大模型，必须要使用 `ModelScope-Free` 下的 `moonshotai/Kimi-K2.5` 模型

### DataFetcher 实现规范

开发 DataFetcher 时，应遵循特定的实现和测试规范，详见 [fetcher-implementation-standard.md](fetcher-implementation-standard.md)。

**核心原则**：
- 分离 API 调用（`_call_api()`）和数据转换（`_transform()`）
- 使用真实 API 调试，使用 mock 测试转换逻辑
- 每个 Fetcher 只需 3-5 个转换测试用例

## 测试策略

### 测试数据规范

所有测试数据必须使用明确的命名前缀，与正式数据隔离：
- 单元测试数据：使用 `test_` 前缀
- 便于清理接口识别和自动删除

### 测试分层原则

- **单元测试**: 大量测试，全 Mock，快速验证逻辑
