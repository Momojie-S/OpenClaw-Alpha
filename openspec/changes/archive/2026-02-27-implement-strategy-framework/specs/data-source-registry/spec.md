## ADDED Requirements

### Requirement: 数据源注册表是全局单例

系统 SHALL 确保 DataSourceRegistry 在整个应用中只有一个实例。

#### Scenario: 多次获取返回同一实例
- **WHEN** 多次调用 `DataSourceRegistry.get_instance()`
- **THEN** 系统返回同一个 DataSourceRegistry 实例

### Requirement: 数据源类型注册

系统 SHALL 支持注册数据源类型，而非实例，延迟实例化到首次使用时。

#### Scenario: 成功注册数据源类型
- **WHEN** 调用 `registry.register(TushareDataSource)`
- **THEN** 系统存储该数据源类，但不立即创建实例

#### Scenario: 注册重名数据源抛出异常
- **WHEN** 注册一个已存在名称的数据源类
- **THEN** 系统抛出 `DuplicateDataSourceError` 异常

### Requirement: 按名称获取数据源实例

系统 SHALL 支持按名称获取数据源实例，首次获取时懒加载创建。

#### Scenario: 首次获取创建实例
- **WHEN** 调用 `registry.get("tushare")` 获取未实例化的数据源
- **THEN** 系统创建该数据源实例并返回

#### Scenario: 后续获取返回同一实例
- **WHEN** 再次调用 `registry.get("tushare")`
- **THEN** 系统返回之前创建的同一实例

#### Scenario: 获取未注册的数据源抛出异常
- **WHEN** 调用 `registry.get("unknown")` 获取未注册的数据源
- **THEN** 系统抛出 `KeyError` 异常

### Requirement: 检查数据源可用性

系统 SHALL 支持检查数据源是否可用（环境配置是否满足）。

#### Scenario: 数据源配置满足返回可用
- **WHEN** 调用 `registry.is_available("tushare")` 且 `TUSHARE_TOKEN` 已配置
- **THEN** 系统返回 `True`

#### Scenario: 数据源配置不满足返回不可用
- **WHEN** 调用 `registry.is_available("tushare")` 且 `TUSHARE_TOKEN` 未配置
- **THEN** 系统返回 `False`

### Requirement: 清理所有数据源资源

系统 SHALL 支持清理所有已初始化的数据源资源。

#### Scenario: 清理所有已初始化的数据源
- **WHEN** 调用 `await registry.close_all()`
- **THEN** 系统调用所有已初始化数据源的 `close()` 方法

### Requirement: 重置注册表

系统 SHALL 支持重置注册表，用于测试场景。

#### Scenario: 重置清除所有注册和实例
- **WHEN** 调用 `registry.reset()`
- **THEN** 系统清除所有已注册的数据源类和已创建的实例
