# 策略框架重构设计

> 版本: v1.0-draft
> 创建时间: 2026-05-17
> 状态: 设计中

---

## 背景

现有 `strategy-framework.md` 设计中，`Strategy` 同时承担「获取数据」和「加工数据」两种职责，导致：

1. **权限声明不精确** - 策略需要多个数据源时，无法表达「数据 A 可从 Tushare 或 AKShare 获取」的语义
2. **组合困难** - 复杂策略组合多个数据源时，权限检查和降级逻辑分散在各处
3. **复用性差** - 同一个数据获取逻辑（如概念板块行情）在不同策略中重复实现

---

## 设计目标

将 Strategy 细分为两个角色：

1. **DataFetcher（数据获取）** - 一个实现只用一种数据源，声明单一数据源权限
2. **DataProcessor（数据加工）** - 组合多个 Fetcher，不直接获取数据，权限自动推导

**核心收益**：
- 权限需求可自动计算：按 data_type 分组，组内 OR，组间 AND
- 数据获取逻辑可复用
- 职责分离，更易测试和维护

---

## 数据格式约定

### 股票代码差异

不同数据源的股票/板块代码格式不同：
- Tushare: `000001.SZ`, `600000.SH`
- AKShare: `000001`, `600000`

### 关联策略

**用 `name` 关联，不用 `code`**：
- `board_name` / `stock_name` 作为跨数据源关联字段
- `code` 仅作为数据源内部标识，不用于关联

**原因**：
- 名称在不同数据源间更稳定
- 简单直接，无需处理代码格式转换

**风险**：名称可能存在细微差异，但板块/股票名称重复和变更的概率很低，可接受。

---

## 架构

### 层级结构

```
┌─────────────────────────────────────────────────────┐
│              DataProcessor（数据加工）               │
│  - 组合多个 DataFetcher                              │
│  - 不直接获取数据，只做计算                          │
│  - 权限 = 组合的 Fetcher 权限的逻辑运算              │
└───────────────────────┬─────────────────────────────┘
                        │ 组合
                        ▼
┌─────────────────────────────────────────────────────┐
│              DataFetcher（数据获取）                 │
│  - 一个实现只用一种数据源                            │
│  - 声明需要的数据源权限（单元素）                    │
│  - 按 data_type 分组，同组可互换                     │
└───────────────────────┬─────────────────────────────┘
                        │ 使用
                        ▼
┌─────────────────────────────────────────────────────┐
│              DataSource（数据源）                    │
│  - 具体 API 客户端封装                               │
│  - 检查配置是否满足                                  │
└─────────────────────────────────────────────────────┘
```

### 权限计算规则

Processor 的权限需求由其组合的 Fetcher 自动推导：

1. **按 data_type 分组** - 同一数据类型的多个 Fetcher 是 OR 关系
2. **组间 AND** - 不同数据类型之间是 AND 关系

**示例**：
```
Processor 需要：
  - concept_board（可从 tushare 或 akshare 获取）
  - sw_industry（只能从 tushare 获取）

权限计算：
  concept_board: tushare OR akshare
  sw_industry:   tushare

最终权限：(tushare OR akshare) AND tushare
```

---

## 核心组件

### DataSource（不变）

保持现有设计，负责数据源客户端封装和配置检查。

### DataFetcher（新增）

**职责**：获取某一类数据，一个实现只用一种数据源。

**关键属性**：
- `name` - Fetcher 标识，如 `tushare_concept`
- `data_type` - 数据类型，如 `concept_board`
- `required_data_source` - 需要的数据源名称
- `priority` - 优先级（数值越大越优先）

**示例**：
```
concept_board 类型下可有两个实现：
  - TushareConceptFetcher（priority=1，优先）
  - AkshareConceptFetcher（priority=0，备选）
```

### DataProcessor（新增）

**职责**：组合多个 Fetcher，加工数据，不直接获取。

**关键属性**：
- `name` - Processor 标识
- `required_fetchers` - 需要的 Fetcher 名称列表

**运行时行为**：
1. 从 FetcherRegistry 获取声明的 Fetcher
2. 检查每个 Fetcher 的数据源是否可用
3. 选择可用的 Fetcher 调用 fetch() 获取数据
4. 执行加工逻辑

### FetcherRegistry（新增）

**职责**：管理所有 Fetcher 实例，支持按 data_type 查询。

**关键方法**：
- `register(fetcher)` - 注册 Fetcher
- `get(name)` - 按名称获取
- `get_by_data_type(data_type)` - 按数据类型获取所有实现
- `get_available(data_type)` - 获取数据类型下所有可用的 Fetcher（数据源配置满足）

---

## 目录结构

```
src/openclaw_alpha/
├── core/
│   ├── data_source.py         # DataSource 基类（不变）
│   ├── fetcher.py             # DataFetcher 基类（新增）
│   ├── processor.py           # DataProcessor 基类（新增）
│   ├── registry.py            # DataSourceRegistry（不变）
│   ├── fetcher_registry.py    # FetcherRegistry（新增）
│   └── exceptions.py          # 异常（扩展）
│
├── data_sources/              # 数据源实现（不变）
│   ├── tushare.py
│   └── akshare.py
│
├── fetchers/                  # 数据获取器（新增）
│   ├── concept_board/
│   │   ├── __init__.py
│   │   ├── tushare.py
│   │   └── akshare.py
│   └── sw_industry/
│       ├── __init__.py
│       └── tushare.py
│
└── processors/                # 数据加工器（新增）
    └── industry_trend/
        ├── __init__.py
        └── processor.py
```

**组织原则**：
- Fetcher 按 data_type 组织，同一类型多个实现放在同一目录
- Processor 独立目录，一个业务场景一个

---

## 与现有设计的关系

| 现有组件 | 新组件 | 说明 |
|---------|-------|------|
| `Strategy`（实现角色） | `DataFetcher` | 职责相同，增加 `data_type` 属性 |
| `Strategy`（入口角色） | `DataProcessor` | 从「选实现」变为「组合 Fetcher」 |
| `DataSourceRegistry` | 不变 | 继续管理数据源 |

**兼容性**：现有 Strategy 代码可继续使用，新功能用 Fetcher + Processor 实现。

---

## 设计决策

### 为什么分离 Fetcher 和 Processor？

| 维度 | DataFetcher | DataProcessor |
|------|-------------|---------------|
| 职责 | 获取数据 | 加工数据 |
| 数据源 | 一个实现只用一种 | 不直接使用 |
| 权限 | 单一数据源 | 组合逻辑运算 |
| 复用 | 高（按 data_type） | 低（业务特定） |

分离后：Fetcher 可跨 Processor 复用，权限声明更精确，测试更容易。

### 为什么 Processor 不直接指定用哪个 Fetcher？

Processor 只声明「我需要哪些 data_type」，运行时根据可用性和优先级自动选择。

好处：
- 新增 Fetcher 实现无需改 Processor
- 不同环境可使用不同的 Fetcher 组合
- 自动降级（优先级高的不可用时用备选）

---

## 后续工作

1. **实现 FetcherRegistry** - 注册表和按 data_type 查询
2. **迁移现有策略** - 将 `sw_industry.py` 改为 Fetcher + Processor
3. **更新主文档** - 合并到 `strategy-framework.md`

---

## 参考资料

- [策略框架设计](./strategy-framework.md) - 原设计文档
- [开发规范](../standards/development-standard.md)
