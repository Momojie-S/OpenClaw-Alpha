# 开发规范

## 开发前准备

开始开发前，请确保已配置标准开发环境（Python、uv 等），并安装项目特定的开发工具，详见 [development-environment.md](development-environment.md)。

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
