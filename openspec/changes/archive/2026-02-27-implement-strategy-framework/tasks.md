## 1. 项目结构

- [x] 1.1 创建 `src/openclaw_alpha/core/` 目录结构
- [x] 1.2 创建 `src/openclaw_alpha/core/__init__.py`，暴露核心类
- [x] 1.3 创建 `src/openclaw_alpha/data_sources/` 目录（占位）
- [x] 1.4 创建 `src/openclaw_alpha/strategies/` 目录（占位）

## 2. 异常类

- [x] 2.1 创建 `src/openclaw_alpha/core/exceptions.py`
- [x] 2.2 实现 `DuplicateDataSourceError` 异常类
- [x] 2.3 实现 `NoAvailableImplementationError` 异常类

## 3. 数据源基类

- [x] 3.1 创建 `src/openclaw_alpha/core/data_source.py`
- [x] 3.2 实现 `DataSource` 泛型基类，定义 `name` 和 `required_config` 抽象属性
- [x] 3.3 实现 `is_available()` 方法，检查环境变量配置
- [x] 3.4 实现 `async initialize()` 方法框架
- [x] 3.5 实现 `async get_client()` 方法，支持懒加载
- [x] 3.6 实现 `async close()` 方法框架
- [x] 3.7 添加 `asyncio.Lock` 保护并发初始化

## 4. 数据源注册表

- [x] 4.1 创建 `src/openclaw_alpha/core/registry.py`
- [x] 4.2 实现 `DataSourceRegistry` 单例模式
- [x] 4.3 实现 `get_instance()` 类方法
- [x] 4.4 实现 `register()` 方法，支持冲突检查
- [x] 4.5 实现 `get()` 方法，支持懒加载实例化
- [x] 4.6 实现 `is_available()` 方法
- [x] 4.7 实现 `async close_all()` 方法
- [x] 4.8 实现 `reset()` 方法

## 5. 策略基类

- [x] 5.1 创建 `src/openclaw_alpha/core/strategy.py`
- [x] 5.2 实现 `Strategy` 泛型基类，定义 `_data_source_names` 属性
- [x] 5.3 实现 `async static get_client()` 静态方法
- [x] 5.4 实现 `async run()` 抽象方法

## 6. 策略入口基类

- [x] 6.1 在 `strategy.py` 中实现 `StrategyEntry` 类
- [x] 6.2 实现 `register()` 方法
- [x] 6.3 实现 `_select_implementation()` 方法，按优先级选择可用实现
- [x] 6.4 实现 `async run()` 方法，自动选择并执行

## 7. 单元测试

- [x] 7.1 创建 `tests/core/` 测试目录
- [x] 7.2 编写 `test_exceptions.py` 测试异常类
- [x] 7.3 编写 `test_data_source.py` 测试数据源基类
- [x] 7.4 编写 `test_registry.py` 测试数据源注册表
- [x] 7.5 编写 `test_strategy.py` 测试策略基类和入口类

## 8. 代码质量

- [x] 8.1 运行 `uv run ruff check src/ tests/` 检查代码
- [x] 8.2 运行 `uv run ruff format src/ tests/` 格式化代码
- [x] 8.3 运行 `uv run pyright src/` 类型检查
