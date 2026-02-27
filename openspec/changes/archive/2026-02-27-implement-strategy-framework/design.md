## Context

OpenClaw-Alpha 是一个股票金融数据获取和分析的技能库。当前项目没有统一的框架来管理不同数据源的能力差异和配置要求。详细设计文档见 `docs/architecture/strategy-framework.md`。

## Goals / Non-Goals

**Goals:**

- 实现数据源注册表（DataSourceRegistry），支持单例管理、懒加载、资源清理、冲突检查
- 实现数据源基类（DataSource），定义能力检查、客户端获取、资源清理接口
- 实现策略基类（Strategy）和策略入口基类（StrategyEntry），支持多实现自动选择
- 实现必要的异常类（NoAvailableImplementationError、DuplicateDataSourceError）

**Non-Goals:**

- 本次不实现具体的数据源（如 TushareDataSource、AkshareDataSource）
- 本次不实现具体的策略（如 StockQuoteStrategy）
- 不实现配置文件自动发现机制

## Decisions

### 1. 目录结构

按职责分离，创建 `core/` 目录存放框架核心代码：

```
src/openclaw_alpha/core/
├── __init__.py
├── exceptions.py    # 异常类
├── registry.py      # DataSourceRegistry
├── data_source.py   # DataSource 基类
└── strategy.py      # Strategy 和 StrategyEntry 基类
```

### 2. 单例模式实现

DataSourceRegistry 使用 `__new__` 方法实现单例，而非装饰器或元类，代码更直观。

### 3. 异步设计

所有 I/O 操作使用 async/await：
- `DataSource.initialize()` - 异步初始化
- `DataSource.get_client()` - 异步获取客户端（自动初始化）
- `DataSource.close()` - 异步清理资源
- `Strategy.run()` - 异步执行

### 4. 懒加载策略

数据源注册时只存储类，首次 `get()` 时才实例化，首次 `get_client()` 时才初始化客户端。

### 5. 类型安全

使用 Python 泛型（Generic）提供类型安全：
- `DataSource[TClient]` - 客户端类型
- `Strategy[TInput, TOutput]` - 输入输出类型

## Risks / Trade-offs

- **全局单例导致测试隔离困难** → 提供 `reset()` 方法，测试前后清理状态
- **静态方法 `get_client()` 类型推断不精确** → 接受此 trade-off，实现处自行处理类型
- **并发调用 `get_client()` 可能重复初始化** → 使用 `asyncio.Lock` 保护初始化过程
