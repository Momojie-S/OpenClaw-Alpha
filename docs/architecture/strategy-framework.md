# 策略框架设计

## 设计目标

为 OpenClaw 提供一套统一的数据获取和处理框架，解决以下问题：

- 支持多种数据源（tushare、akshare 等），每种数据源有不同的配置要求
- 同一数据可以有多种实现方式，依赖不同的数据源
- 运行时自动选择当前环境可用的实现
- 职责分离：Fetcher（入口调度）与 FetchMethod（具体实现）解耦

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

### 数据获取器

每个 fetcher 目录包含一个入口类和多个数据源实现。

**Fetcher（入口）**：负责注册和调度，选择可用的实现执行。

**FetchMethod（实现）**：负责具体的数据获取逻辑，绑定单一数据源。

**命名规范**：
- 入口类：`XxxFetcher extends Fetcher`
- 实现类：`XxxFetcher{Tushare|Akshare} extends FetchMethod`

**注册方式**：在入口类的 `__init__` 中注册各个实现，声明优先级。

**调用方式**：`__init__.py` 暴露 `fetch()` 函数，内部调用入口类实例。

```
concept_fetcher/
├── __init__.py            # 暴露 fetch() 函数
├── concept_fetcher.py     # ConceptFetcher extends Fetcher（注册实现）
├── tushare.py             # ConceptFetcherTushare extends FetchMethod
└── akshare.py             # ConceptFetcherAkshare extends FetchMethod
```

### 数据格式约定

**用 `name` 关联，不用 `code`**：
- 不同数据源的代码格式不同（如 Tushare: `000001.SZ`，AKShare: `000001`）
- 使用 `board_name` / `stock_name` 作为跨数据源关联字段
- `code` 仅作为数据源内部标识

### 数据加工器（Processor）

Processor 是可执行的脚本，大模型通过命令行调用，负责协调 Fetcher 获取数据并加工。

**调用方式**：
```bash
# 直接执行脚本
uv run --env-file .env python skills/{skill_name}/scripts/{scenario}_processor/{scenario}_processor.py [参数]

# 模块方式
uv run --env-file .env python -m skills.{skill_name}.scripts.{scenario}_processor.{scenario}_processor [参数]
```

**职责**：
- 提供命令行入口（`__main__`）
- 解析命令行参数
- 调用 Fetcher 获取数据
- 加工数据（计算指标、筛选 Top N 等）
- 输出结果（打印或保存到文件）

**入参**：每个 Processor 定义自己的命令行参数，按 Skill 需要灵活设计。

**命名规范**：
- 目录：`{scenario}_processor/`
- 脚本：`{scenario}_processor.py`
- 暴露：`__main__` 入口

```
industry_trend_processor/
├── __init__.py            # 暴露 process() 函数（可选）
└── industry_trend_processor.py  # Processor 逻辑 + __main__
```

### 异常

- **NoAvailableMethodError**：当某 fetcher 的所有实现都不可用时抛出

## 类层级结构

```
框架层（core/）
────────────────────────────────────
DataSourceRegistry      数据源注册表（全局单例）
DataSource<TClient>     数据源基类
Fetcher                 Fetcher 入口基类（调度）
FetchMethod             Fetcher 实现基类

业务层（实现）
────────────────────────────────────
TushareDataSource       extends DataSource
AkshareDataSource       extends DataSource

# Fetcher 实现（按业务场景组织）
ConceptFetcher          extends Fetcher（入口）
├── ConceptFetcherTushare extends FetchMethod
└── ConceptFetcherAkshare extends FetchMethod

# Processor 实现（脚本执行）
IndustryTrendProcessor  可执行脚本
└── 命令行参数解析
```

## 目录结构

```
OpenClaw-Alpha/
├── skills/                         # SKILL 目录（文档 + 代码）
│   └── {skill_name}/
│       ├── SKILL.md                # 能力说明 + 分析指引
│       └── scripts/                # Skill 代码
│           ├── __init__.py
│           ├── {data_type}_fetcher/
│           │   ├── __init__.py
│           │   ├── {data_type}_fetcher.py
│           │   ├── tushare.py
│           │   └── akshare.py
│           └── {scenario}_processor/
│               ├── __init__.py
│               └── {scenario}_processor.py
│
├── src/openclaw_alpha/
│   ├── core/                       # 框架核心（基类）
│   │   ├── exceptions.py
│   │   ├── data_source.py
│   │   ├── fetcher.py
│   │   └── processor_utils.py
│   └── data_sources/               # 数据源实现
│       ├── tushare.py
│       └── akshare.py
│
└── pyproject.toml                  # 包配置（注册 openclaw_alpha）
```

**组织原则**：
- 每个 Skill 自包含：文档（SKILL.md）+ 代码（scripts/）在同一目录
- `src/openclaw_alpha/core/` - 框架基类，通过 pyproject.toml 注册为包
- `src/openclaw_alpha/data_sources/` - 数据源实现

**导入方式**：
- 导入基类：`from openclaw_alpha.core.fetcher import Fetcher`
- Skill 内部：相对路径 `from .xxx import xxx`

**运行方式**：
```bash
# 直接执行脚本
uv run --env-file .env python skills/{skill_name}/scripts/{scenario}_processor/{scenario}_processor.py

# 模块方式
uv run --env-file .env python -m skills.{skill_name}.scripts.{scenario}_processor.{scenario}_processor
```

**命名规范**：
- Fetcher 目录：`{data_type}_fetcher/`
- 入口类：`{Data_type}Fetcher extends Fetcher`
- 实现类：`{Data_type}Fetcher{Tushare|Akshare} extends FetchMethod`

## 基类接口

### DataSource

- `name` - 数据源名称
- `required_config` - 所需的环境变量配置项
- `is_available()` - 检查当前环境是否满足要求
- `get_client()` - 获取数据源客户端（懒加载）
- `close()` - 清理资源

### Fetcher（入口基类）

- `register(method, priority)` - 注册实现
- `fetch(params)` - 选择可用实现并执行
- `_select_available()` - 按优先级选择数据源可用的实现

### FetchMethod（实现基类）

- `name` - Method 标识
- `required_data_source` - 需要的数据源名称
- `priority` - 优先级
- `fetch(params)` - 执行数据获取

### Processor

可执行脚本，通过命令行调用，无统一基类要求。

**典型结构**：
- `XxxProcessor` - 处理逻辑类（可选）
- `process()` - 主入口方法
- `__main__` - 命令行入口（必需）

**职责**：
- 解析命令行参数
- 调用 Fetcher 获取数据
- 加工数据（计算、筛选、排序）
- 输出结果（打印或保存到文件）

## 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                        大模型                           │
│                                                         │
│   exec: 运行 processor 脚本 → 读取输出 → 分析结果      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     Processor（脚本）                    │
│                                                         │
│   1. 解析命令行参数                                     │
│   2. 调用 Fetcher 获取数据                              │
│   3. 加工数据（计算指标、筛选 Top N）                   │
│   4. 输出结果（打印或保存）                             │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Fetcher（入口）                        │
│                                                         │
│   1. 注册多个 FetchMethod（按优先级）                    │
│   2. 选择数据源可用的实现                               │
│   3. 调用 Method.fetch() 获取数据                       │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
   │FetchMethod  │ │FetchMethod  │ │FetchMethod  │
   │  Tushare    │ │  Akshare    │ │  Others     │
   └─────────────┘ └─────────────┘ └─────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  DataSourceRegistry                      │
│                  (全局单例，懒加载)                       │
└─────────────────────────────────────────────────────────┘
```

## 设计决策

### 为什么把脚本放在 skills/{skill_name}/scripts/ 下？

**符合 OpenClaw skill 规范**：
- 文档（SKILL.md）和代码（scripts/）在同一目录
- Skill 自包含，方便复制和分发

**导入方式清晰**：
- 基类通过 `openclaw_alpha.core.*` 导入（pyproject.toml 注册）
- Skill 内部用相对路径 `from .`

**简化结构**：
- 删除 `src/openclaw_alpha/skills/` 目录
- `src/` 只保留框架核心（core、data_sources）

### 为什么分离 Fetcher、FetchMethod 和 Processor？

| 维度 | Fetcher（入口） | FetchMethod（实现） | Processor |
|------|----------------|-------------------|-----------|
| 职责 | 调度、选择 | 数据获取 | 数据加工、输出 |
| 数据源 | 不绑定 | 绑定单一数据源 | 不直接绑定 |
| 调用方 | Processor | Fetcher | 大模型（命令行） |
| 形态 | Python 类 | Python 类 | 可执行脚本 |

分离后：大模型通过命令行执行 Processor，Processor 调用 Fetcher 获取数据，不用关心数据源细节。

### 为什么 Processor 用命令行参数？

- 符合脚本调用习惯
- 大模型通过 exec 执行命令，参数直观
- 每个 Skill 按需定义参数，灵活适配业务场景

### 为什么用 name 关联而非 code？

**问题**：不同数据源的代码格式不同
- Tushare: `000001.SZ`, `600000.SH`
- AKShare: `000001`, `600000`

**解决**：用 `board_name` / `stock_name` 关联
- 名称在不同数据源间更稳定
- 简单直接，无需处理代码格式转换

### 为什么用异步？

金融数据获取是 I/O 密集型操作：
- 网络请求耗时，异步可并发执行
- 适配 asyncio 生态

### 为什么用优先级而非随机选择？

优先级允许根据数据质量、速度、成本等因素选择最佳数据源。

---

## 参考资料

- [开发规范](../standards/development-standard.md)
- [Fetcher 实现规范](../standards/fetcher-implementation-standard.md)
