# 策略框架设计

> **v2.0 - 2026-03-04**：扩展为包含 DataFetcher、DataProcessor、FetcherRegistry 的分层架构

## 设计目标

为 OpenClaw 提供一套统一的策略执行框架，解决以下问题：

- 支持多种数据源（tushare、akshare 等），每种数据源有不同的配置要求
- 同一策略可以有多种实现方式，依赖不同的数据源
- 运行时自动选择当前环境可用的实现
- 策略调用方无需关心具体使用了哪个数据源
- **v2.0 新增**：职责分离，数据获取（DataFetcher）与数据加工（DataProcessor）解耦
- **v2.0 新增**：权限自动推导，按 data_type 分组计算

## 核心概念

### 数据源注册表（DataSourceRegistry）

全局单例，管理所有数据源的实例。职责：

- 注册数据源类型（按名称）
- 按名称获取数据源实例（单例）
- 懒加载：首次获取时创建实例

### 数据源（DataSource）

数据源是获取金融数据的来源，每个数据源有自己的能力要求。

**能力要求**：数据源运行所需的环境配置，例如：
- tushare 需要 `TUSHARE_TOKEN`
- akshare 无需任何配置

**懒加载**：数据源客户端在首次调用 `get_client()` 时初始化，而非注册时。

### 策略（Strategy）

策略是统一的执行单元，有两种角色：

- **具体实现**：声明依赖的数据源名称列表，实现具体的获取逻辑
- **策略入口**：管理多个具体实现，运行时自动选择可用的实现执行

两者都是 Strategy，只是职责不同。

**数据源获取**：Strategy 基类提供静态方法 `get_client(name)`，实现通过它直接获取数据源客户端。

**多数据源支持**：一个实现可以绑定多个数据源，只有当所有绑定的数据源都可用时，该实现才会被选中。

**异步执行**：所有策略的 `run()` 方法都是异步的，适应 I/O 密集型的数据获取场景。

### 数据获取器（DataFetcher）- v2.0 新增

DataFetcher 专门负责数据获取，一个实现只用一种数据源。

**关键属性**：
- `name` - Fetcher 标识，如 `tushare_concept`
- `data_type` - 数据类型，如 `concept_board`（按此分组，同组可互换）
- `required_data_source` - 需要的数据源名称（单元素）
- `priority` - 优先级（数值越大越优先）

**运行时行为**：
1. 从 DataSourceRegistry 获取数据源客户端
2. 调用 API 获取原始数据
3. 转换为标准格式返回

**示例**：
```
concept_board 类型下可有两个实现：
  - TushareConceptFetcher（priority=1，优先）
  - AkshareConceptFetcher（priority=0，备选）
```

### 数据加工器（DataProcessor）- v2.0 新增

DataProcessor 组合多个 Fetcher，只做数据加工，不直接获取数据。

**关键属性**：
- `name` - Processor 标识
- `required_fetchers` - 需要的 Fetcher 名称列表

**运行时行为**：
1. 从 FetcherRegistry 获取声明的 Fetcher
2. 检查每个 Fetcher 的数据源是否可用
3. 选择可用的 Fetcher 调用 fetch() 获取数据
4. 执行加工逻辑

**权限自动推导**：
- 按 data_type 分组，组内 OR（同类型 Fetcher 任一可用即可）
- 组间 AND（不同类型的 Fetcher 都需要可用）

### Fetcher 注册表（FetcherRegistry）- v2.0 新增

全局单例，管理所有 Fetcher 实例。

**关键方法**：
- `register(fetcher)` - 注册 Fetcher
- `get(name)` - 按名称获取
- `get_by_data_type(data_type)` - 按数据类型获取所有实现
- `get_available(data_type)` - 获取数据类型下所有可用的 Fetcher

### 数据格式约定 - v2.0 新增

**用 `name` 关联，不用 `code`**：
- 不同数据源的代码格式不同（如 Tushare: `000001.SZ`，AKShare: `000001`）
- 使用 `board_name` / `stock_name` 作为跨数据源关联字段
- `code` 仅作为数据源内部标识

### 异常

- **NoAvailableImplementationError**：当所有实现的数据源都不可用时抛出
- **NoAvailableFetcherError** - v2.0 新增：当某数据类型的所有 Fetcher 都不可用时抛出
- **DuplicateFetcherError** - v2.0 新增：注册重名 Fetcher 时抛出

## 类层级结构

### v1.0 - Strategy 模式

框架提供三个核心组件，业务层实现具体的数据源和策略。

```
框架层（core/）
────────────────────────────────────
DataSourceRegistry      数据源注册表（全局单例）
DataSource<TClient>     数据源基类
Strategy<TInput,TOutput> 策略基类

业务层（实现）
────────────────────────────────────
TushareDataSource       extends DataSource
AkshareDataSource       extends DataSource

StockQuoteStrategy      extends Strategy（入口角色）
├── StockQuoteTushare   extends Strategy（实现角色）
└── StockQuoteAkshare   extends Strategy（实现角色）
```

### v2.0 - Fetcher + Processor 模式（推荐）

新增三个核心组件，实现职责分离。

```
框架层（core/）
────────────────────────────────────
DataSourceRegistry      数据源注册表（全局单例）
FetcherRegistry         Fetcher 注册表（全局单例）
DataSource<TClient>     数据源基类
DataFetcher<TInput,TOutput>   数据获取器基类
DataProcessor<TInput,TOutput> 数据加工器基类
Strategy<TInput,TOutput>      策略基类（兼容保留）

业务层（实现）
────────────────────────────────────
TushareDataSource       extends DataSource
AkshareDataSource       extends DataSource

# Fetcher 实现（按 data_type 组织）
ConceptTushareFetcher   extends DataFetcher
ConceptAkshareFetcher   extends DataFetcher
SwIndustryTushareFetcher extends DataFetcher

# Processor 实现（按业务场景组织）
IndustryTrendProcessor  extends DataProcessor
```

**推荐使用 v2.0 模式**，职责更清晰，权限更精确。

## 目录结构

### v1.0 - Strategy 模式

```
src/openclaw_alpha/
├── core/                      # 框架核心（基类）
│   ├── __init__.py
│   ├── exceptions.py          # 自定义异常
│   ├── registry.py            # DataSourceRegistry
│   ├── data_source.py         # DataSource 基类
│   └── strategy.py            # Strategy 基类
│
├── data_sources/              # 数据源实现
│   ├── __init__.py
│   ├── tushare.py             # Tushare 数据源
│   └── akshare.py             # Akshare 数据源
│
└── strategies/                # 策略目录
    └── stock_quote/           # 一个策略一个 package
        ├── __init__.py        # 入口，暴露 Strategy
        ├── strategy.py        # StockQuoteStrategy（入口）
        ├── tushare.py         # StockQuoteTushare（实现）
        └── akshare.py         # StockQuoteAkshare（实现）
```

### v2.0 - Fetcher + Processor 模式

```
src/openclaw_alpha/
├── core/                      # 框架核心（基类）
│   ├── __init__.py
│   ├── exceptions.py          # 自定义异常（扩展）
│   ├── registry.py            # DataSourceRegistry
│   ├── fetcher_registry.py    # FetcherRegistry（新增）
│   ├── data_source.py         # DataSource 基类
│   ├── fetcher.py             # DataFetcher 基类（新增）
│   └── processor.py           # DataProcessor 基类（新增）
│
├── data_sources/              # 数据源实现
│   ├── __init__.py
│   ├── tushare.py
│   └── akshare.py
│
├── fetchers/                  # 数据获取器（新增）
│   ├── __init__.py
│   ├── concept_board/         # 按 data_type 组织
│   │   ├── __init__.py
│   │   ├── models.py          # 数据模型
│   │   ├── tushare.py         # Tushare 实现
│   │   └── akshare.py         # AKShare 实现
│   └── sw_industry/
│       ├── __init__.py
│       ├── models.py
│       └── tushare.py
│
├── processors/                # 数据加工器（新增）
│   ├── __init__.py
│   └── industry_trend/        # 按业务场景组织
│       ├── __init__.py
│       ├── models.py
│       └── processor.py
│
└── strategies/                # 策略目录（兼容保留）
    └── stock_quote/
        ├── __init__.py
        └── ...
```

**组织原则**：
- Fetcher 按 `data_type` 组织，同一类型多个实现放在同一目录
- Processor 按业务场景组织，一个场景一个目录
- Strategy 保留用于兼容，新功能建议用 Fetcher + Processor

## 基类接口定义

### DataSourceRegistry

```python
from typing import Type


class DuplicateDataSourceError(Exception):
    """数据源名称重复"""


class DataSourceRegistry:
    """数据源注册表，管理数据源单例"""

    _instance: "DataSourceRegistry | None" = None
    _data_source_classes: dict[str, Type[DataSource]]  # 存储类，延迟实例化
    _data_source_instances: dict[str, DataSource]  # 存储实例

    def __new__(cls) -> "DataSourceRegistry":
        """单例模式"""
        pass

    @classmethod
    def get_instance(cls) -> "DataSourceRegistry":
        """获取全局单例"""
        pass

    def register(self, data_source_class: Type[DataSource]) -> None:
        """
        注册数据源类型（按类注册，延迟实例化）

        Raises:
            DuplicateDataSourceError: 名称已存在
        """
        pass

    def get(self, name: str) -> DataSource:
        """按名称获取数据源实例（懒加载，首次时创建）"""
        pass

    def is_available(self, name: str) -> bool:
        """检查数据源是否可用"""
        pass

    async def close_all(self) -> None:
        """清理所有已初始化的数据源资源"""
        pass

    def reset(self) -> None:
        """重置注册表（用于测试）"""
        pass
```

### DataSource

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TClient = TypeVar("TClient")


class DataSource(ABC, Generic[TClient]):
    """数据源基类，泛型 TClient 为客户端类型"""

    @property
    @abstractmethod
    def name(self) -> str:
        """数据源名称，用于注册表索引"""
        pass

    @property
    @abstractmethod
    def required_config(self) -> list[str]:
        """所需的环境变量配置项列表"""
        pass

    def is_available(self) -> bool:
        """检查当前环境是否满足数据源要求"""
        pass

    async def initialize(self) -> None:
        """初始化数据源，创建客户端连接（异步）"""
        pass

    async def get_client(self) -> TClient:
        """获取数据源客户端（懒加载，自动初始化）"""
        pass

    async def close(self) -> None:
        """清理资源（连接池、会话等）"""
        pass
```

### Strategy

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class Strategy(ABC, Generic[TInput, TOutput]):
    """策略基类，支持泛型的入参和出参类型"""

    _data_source_names: list[str]  # 声明依赖的数据源名称（用于可用性检查）

    @staticmethod
    async def get_client(name: str) -> TClient:
        """从注册表获取数据源客户端（便捷方法）"""
        pass

    @abstractmethod
    async def run(self, input: TInput) -> TOutput:
        """执行策略逻辑（异步）"""
        pass


class StrategyEntry(Strategy[TInput, TOutput]):
    """策略入口基类，管理多个实现并自动选择"""

    def __init__(self) -> None:
        self._implementations: list[tuple[list[str], Strategy[TInput, TOutput], int]] = []

    def register(
        self,
        impl: Strategy[TInput, TOutput],
        priority: int = 0,
    ) -> None:
        """注册一个实现（实现自带 _data_source_names）"""
        pass

    async def run(self, input: TInput) -> TOutput:
        """选择可用的实现并执行（异步）"""
        pass

    def _select_implementation(self) -> Strategy[TInput, TOutput]:
        """选择优先级最高且数据源都可用的实现，无可用时抛出 NoAvailableImplementationError"""
        pass
```

### 异常

```python
class NoAvailableImplementationError(Exception):
    """所有实现的数据源都不可用"""

    def __init__(self, strategy_name: str, checked_implementations: list[str]):
        pass


class DuplicateDataSourceError(Exception):
    """数据源名称重复"""

    def __init__(self, name: str):
        pass
```

## 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                  DataSourceRegistry                      │
│                  (全局单例，懒加载)                       │
│                                                         │
│   register(TushareDataSource)                          │
│   register(AkshareDataSource)                          │
│                                                         │
│   get("tushare") → TushareDataSource 实例              │
│   get("akshare") → AkshareDataSource 实例              │
│                                                         │
│   close_all() → 清理所有资源                            │
│   reset() → 重置注册表（测试用）                         │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │ Strategy.get_client(name)
                          │
┌─────────────────────────────────────────────────────────┐
│                     调用方                               │
│         await strategy.run(input) → output             │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              StockQuoteStrategy（入口角色）               │
│                                                         │
│   1. 遍历所有注册的实现                                   │
│   2. 检查每个实现声明的数据源是否可用                      │
│   3. 选择优先级最高的可用实现                             │
│   4. await 执行实现并返回结果                            │
│   5. 无可用实现 → 抛出 NoAvailableImplementationError   │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
   │  Strategy   │ │  Strategy   │ │  Strategy   │
   │  (实现角色)  │ │  (实现角色)  │ │  (实现角色)  │
   │             │ │             │ │             │
   │ _data_      │ │ _data_      │ │ _data_      │
   │ source_     │ │ source_     │ │ source_     │
   │ names:      │ │ names:      │ │ names:      │
   │ ["tushare", │ │ ["akshare"] │ │ ["others"]  │
   │  "akshare"] │ │             │ │             │
   │             │ │             │ │             │
   │ Priority: 1 │ │ Priority: 2 │ │ Priority: 3 │
   └─────────────┘ └─────────────┘ └─────────────┘
          │
          │ await Strategy.get_client("tushare")
          ▼
   ┌─────────────────────────────────┐
   │       DataSourceRegistry        │
   │       .get("tushare")           │
   │              │                  │
   │              ▼                  │
   │       TushareDataSource         │
   │       (单例实例)                 │
   │              │                  │
   │              ▼                  │
   │       get_client() → client     │
   └─────────────────────────────────┘
```

## 运行流程

```
1. 启动阶段
   ├── DataSourceRegistry.get_instance() 获取单例
   └── registry.register(TushareDataSource) 注册数据源类型（重复名称抛异常）

2. 策略初始化阶段
   ├── 创建 StrategyEntry
   └── entry.register(impl) 注册实现（实现自带数据源依赖声明）

3. 执行阶段
   ├── await entry.run(input)
   ├── _select_implementation() 检查数据源可用性
   │   ├── 遍历实现，按优先级排序
   │   ├── 检查每个实现的数据源是否可用
   │   └── 返回第一个可用的实现，否则抛异常
   └── await impl.run(input)
       ├── await Strategy.get_client("tushare")
       ├── registry.get("tushare") → 单例
       ├── ds.get_client() → 懒加载初始化
       └── client.xxx() 调用 API

4. 清理阶段
   └── await registry.close_all() 清理所有数据源资源
```

## 泛型设计

策略使用泛型支持不同的入参和出参类型：

- `TInput`：策略的输入类型
- `TOutput`：策略的输出类型

**约束**：同一策略的多个实现必须使用相同的 `TInput` 和 `TOutput`，保证实现可互换。

**建议**：当入参字段较多时，使用 dataclass 封装输入结构。

## 环境配置

数据源的能力要求通过环境变量满足：

- 配置项在 `.env` 文件中定义
- 运行时通过 `uv run --env-file .env` 加载
- 数据源负责检查自身所需配置是否存在

## 扩展性

### 新增数据源

1. 定义新的 DataSource 类
2. 在启动时注册到 Registry

### 新增策略实现

1. 定义新的 Strategy 子类
2. 声明 `_data_source_names`
3. 注册到对应的 StrategyEntry

### 新增策略

1. 创建新的策略 package
2. 定义 StrategyEntry 和多个实现
3. 在 `__init__.py` 中暴露入口

## 设计决策

### 为什么需要 DataSourceRegistry？

- **单例管理**：多个策略实现共享同一数据源实例，节省连接资源
- **懒加载**：注册类型而非实例，按需创建
- **解耦**：实现不需要持有数据源实例，通过注册表按名称获取
- **资源清理**：统一管理数据源的生命周期，支持批量清理

### 为什么 Strategy.get_client() 是静态方法？

- **简洁**：实现中直接 `await Strategy.get_client("tushare")`，无需先获取数据源再获取客户端
- **无状态**：Strategy 基类不需要持有数据源实例，减少状态管理
- **便捷**：子类只需声明 `_data_source_names` 用于可用性检查，实际获取通过静态方法

### 为什么统一用 Strategy 而非分开 Strategy 和 StrategyImpl？

简化设计。Strategy 和 StrategyImpl 本质上都是"可执行的单元"，只是职责不同：
- 实现角色：只实现 `run()` 方法，声明数据源依赖
- 入口角色：实现 `run()` + 管理实现列表 + 选择逻辑

统一用 Strategy 减少概念数量，代码更简洁。

### 为什么用异步？

金融数据获取是 I/O 密集型操作：
- 网络请求耗时，异步可并发执行
- 适配 asyncio 生态，与 FastAPI 等框架兼容

### 为什么用懒加载？

- 按需初始化，避免启动时创建不用的客户端
- 首次使用时才检查配置，便于测试和调试

### 为什么用优先级而非随机选择？

优先级允许使用者根据数据质量、速度、成本等因素选择最佳数据源。

### 为什么数据源自带能力检查？

数据源最清楚自己需要什么配置，将检查逻辑内聚在数据源中，策略无需关心细节。

### 为什么使用泛型而非 Any？

泛型提供类型安全，IDE 支持更好，同时保持灵活性让不同策略定义自己的类型。

### 为什么支持一个实现绑定多个数据源？

某些复杂策略需要组合多个数据源的能力：
- tushare 提供历史数据 + akshare 提供实时行情
- 不同数据源覆盖不同市场（A股 vs 港股）

这种设计允许策略根据实际能力提供"完整版"和"精简版"两种实现，当某些数据源不可用时自动降级。

---

## v2.0 新增设计决策

### 为什么分离 DataFetcher 和 DataProcessor？

| 维度 | DataFetcher | DataProcessor |
|------|-------------|---------------|
| 职责 | 获取数据 | 加工数据 |
| 数据源 | 一个实现只用一种 | 不直接使用 |
| 权限 | 单一数据源 | 组合逻辑运算 |
| 复用 | 高（按 data_type） | 低（业务特定） |

分离后：Fetcher 可跨 Processor 复用，权限声明更精确，测试更容易。

### 为什么 DataProcessor 用 `required_fetchers` 而非 `required_data_types`？

**当前决策**：使用 `required_fetchers`（Fetcher 名称列表）

**原因**：
- 更明确：Processor 直接声明需要的 Fetcher 名称
- 适合当前阶段：简化设计，减少抽象层
- 易于调试：可以精确定位使用了哪个 Fetcher

**未来考虑**：如果需要更灵活的自动选择，可改为 `required_data_types`，运行时自动查找可用的 Fetcher。

### 为什么用 name 关联而非 code？

**问题**：不同数据源的代码格式不同
- Tushare: `000001.SZ`
- AKShare: `000001`

**决策**：用 `board_name` / `stock_name` 作为关联字段

**原因**：
- 名称在不同数据源间更稳定
- 简单直接，无需处理代码格式转换

**风险**：名称可能存在细微差异，但板块/股票名称重复和变更的概率很低，可接受。

### 为什么不一次性迁移所有现有实现？

**决策**：渐进式迁移，优先迁移核心功能

**原因**：
- 降低风险：避免大规模重构引入问题
- 验证设计：先让新架构在部分场景验证
- 逐步完善：根据使用反馈调整设计

**当前状态**：
- ✅ board_concept 命令已迁移到 Fetcher
- ⏸️ sw_industry 命令待迁移
- ⏸️ 其他命令按需迁移

---

## v2.0 新增设计决策

### 为什么分离 DataFetcher 和 DataProcessor？

| 维度 | DataFetcher | DataProcessor |
|------|-------------|---------------|
| 职责 | 获取数据 | 加工数据 |
| 数据源 | 一个实现只用一种 | 不直接使用 |
| 权限 | 单一数据源 | 组合逻辑运算 |
| 复用 | 高（按 data_type） | 低（业务特定） |

分离后：Fetcher 可跨 Processor 复用，权限声明更精确，测试更容易。

### 为什么 DataProcessor 用 required_fetchers 而非 required_data_types？

**采用 `required_fetchers`**：Processor 直接声明需要的 Fetcher 名称。

**原因**：
- **更明确**：直接知道用了哪些 Fetcher，没有歧义
- **适合当前阶段**：简化设计，减少抽象层
- **易于调试**：从声明就能看出依赖关系

**示例**：
```python
class IndustryTrendProcessor:
    required_fetchers = [
        "tushare_concept",  # 或 "akshare_concept"
        "tushare_sw_industry",
    ]
```

**vs `required_data_types` 方案**：
```python
class IndustryTrendProcessor:
    required_data_types = ["concept_board", "sw_industry"]
    # 运行时从 Registry 获取该类型的所有 Fetcher
```

`required_data_types` 更灵活但更抽象，`required_fetchers` 更直接更适合当前阶段。

### 为什么用 name 关联而非 code？

**问题**：不同数据源的代码格式不同
- Tushare: `000001.SZ`, `600000.SH`
- AKShare: `000001`, `600000`

**解决**：用 `board_name` / `stock_name` 关联
- 名称在不同数据源间更稳定
- 简单直接，无需处理代码格式转换

**风险**：名称可能存在细微差异，但板块/股票名称重复和变更的概率很低，可接受。

### 为什么不一次性迁移所有现有实现？

**决策**：渐进式迁移，优先迁移核心功能

**原因**：
- 降低风险：避免大规模重构引入问题
- 验证设计：先让新架构在部分场景验证
- 逐步完善：根据使用反馈调整设计

**当前状态**：
- ✅ board_concept 命令已迁移到 Fetcher
- ⏸️ sw_industry 命令待迁移
- ⏸️ 其他命令按需迁移

---

## 迁移路径

### v1.0 → v2.0

**保留**：
- DataSource 基类和 Registry
- Strategy 基类（兼容）
- 现有 strategies/ 目录

**新增**：
- DataFetcher 基类和 FetcherRegistry
- DataProcessor 基类
- fetchers/ 目录
- processors/ 目录

**迁移步骤**：
1. 新功能用 Fetcher + Processor 实现
2. 逐步将高频使用的 Strategy 改为 Fetcher + Processor
3. 低频使用的 Strategy 保持不变
4. 最终两种模式共存，根据场景选择

---

## 参考资料

- [OpenSpec specs](../../openspec/specs/) - 当前行为规范
- [开发规范](../standards/development-standard.md)
