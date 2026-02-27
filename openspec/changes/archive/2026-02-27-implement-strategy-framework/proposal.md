## Why

OpenClaw 需要一套统一的策略执行框架来支持多数据源的股票金融数据获取。当前项目没有统一的框架来管理不同数据源（如 tushare、akshare）的能力差异和配置要求，导致：
- 每个策略实现需要手动处理数据源选择逻辑
- 数据源配置检查分散在各处
- 无法优雅地处理数据源不可用的降级场景

## What Changes

新增策略框架核心组件：

- **DataSourceRegistry**: 全局数据源注册表，管理数据源单例，支持懒加载和资源清理
- **DataSource 基类**: 数据源抽象，定义能力检查、客户端获取、资源清理等接口
- **Strategy 基类**: 策略抽象，支持泛型入参出参，提供静态方法获取数据源客户端
- **StrategyEntry 基类**: 策略入口，管理多个实现，运行时自动选择可用的实现执行
- **异常类**: `NoAvailableImplementationError`、`DuplicateDataSourceError`

## Capabilities

### New Capabilities

- `data-source-registry`: 数据源注册表，管理数据源单例、懒加载、资源清理、冲突检查
- `data-source`: 数据源基类，定义能力检查、客户端获取、资源清理接口
- `strategy`: 策略框架核心，包含 Strategy 基类和 StrategyEntry 基类，支持多实现自动选择

### Modified Capabilities

（无）

## Impact

- 新增 `src/openclaw_alpha/core/` 目录，包含框架核心代码
- 新增 `src/openclaw_alpha/data_sources/` 目录，后续实现具体数据源
- 新增 `src/openclaw_alpha/strategies/` 目录，后续实现具体策略
- 依赖项无变化
